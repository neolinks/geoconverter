import shapefile
import zipfile
import io

import tempfile
from io import BytesIO
from geojson import Feature, Point, FeatureCollection
from pyproj import Proj, transform, CRS, Transformer
from kml import build_layers
import xml.dom.minidom as md


required_suffixes = ["shp", "shx", "dbf", "prj"]


def _set_precision(coords, precision):
    result = []
    try:
        return round(coords, int(precision))
    except TypeError:
        for coord in coords:
            result.append(_set_precision(coord, precision))
    return result


def coord_precision(features, precision):
    for feature in features:
        coords = _set_precision(feature['geometry']['coordinates'], precision)
        feature['geometry']['coordinates'] = coords

        yield feature


def tranform_geojson(geom_type="point", features=[], input_crs=4326, output_crs=3857):

    destination = CRS.from_epsg(input_crs)
    target = CRS.from_epsg(output_crs)
    transformer = Transformer.from_crs(int(input_crs), int(output_crs))
    # Define dictionary representation of output feature collection
    fc_out = {'features': [],
              'type': 'FeatureCollection'}
    geom = geom_type
    # Iterate through each feature of the feature collection

    """ NULL = 0
    POINT = 1
    POLYLINE = 3
    POLYGON = 5
    MULTIPOINT = 8
    POINTZ = 11
    POLYLINEZ = 13
    POLYGONZ = 15
    MULTIPOINTZ = 18
    POINTM = 21
    POLYLINEM = 23
    POLYGONM = 25
    MULTIPOINTM = 28
    MULTIPATCH = 31 """

    for feature in features:
        counter = 0
        feature_out = feature.copy()
        new_coords = []
        # Project/transform coordinate pairs of each ring
        # (iteration required in case geometry type is MultiPolygon, or there are holes)
        geom_type = feature['geometry']['type']
        if (geom_type == "Point"):
            x1, y1 = (feature['geometry']['coordinates'])
            x2, y2 = transformer.transform(x1, y1)
            feature_out['geometry']['coordinates'] = [x2, y2]
            fc_out['features'].append(feature_out)

        else:
            for ring in feature['geometry']['coordinates']:

                res = [list(ele) for ele in list(ring)]
                x2, y2 = transformer.transform(*zip(*res))
                new_coords.append(zip(x2, y2))
                # Append transformed coordinates to output feature
                feature_out['geometry']['coordinates'] = new_coords
                # Append feature to output featureCollection
                fc_out['features'].append(feature_out)

    return (fc_out)


def checkExtension(fileName):
    return '.' in fileName and \
        fileName.rsplit('.', 1)[1].lower() == "zip"


def validate_shp_files(filelist):
    has_suffix = {}
    for suffix in required_suffixes:
        has_suffix[suffix] = False
    for name in filelist:
        extension = name.split(".")[1].lower()
        if extension in required_suffixes:
            has_suffix[extension] = True
    for suffix in required_suffixes:
        if not has_suffix[suffix]:
            return "Zip arşivinde "+suffix+" dosyası eksik."
    return True


def transform_polygons(reader):
    pass


def import_data(zipfile_ob, **kwargs):

    p_response = {"status": 0, "message": "", "data": None}
    geojson = {}

    validate = validate_shp_files(zipfile_ob.namelist())
    if not validate == True:
        return validate

    try:
        dbfname, prjname, shpname, shxname = [
            name for name in zipfile_ob.namelist() if (name.split(".")[1] in required_suffixes)]
        cloudshp = BytesIO(zipfile_ob.read(shpname))
        cloudshx = BytesIO(zipfile_ob.read(shxname))
        clouddbf = BytesIO(zipfile_ob.read(dbfname))
        cloudprj = BytesIO(zipfile_ob.read(prjname))
        reader = shapefile.Reader(shp=cloudshp, shx=cloudshx, dbf=clouddbf)

    except:
        # response["status"]=0
        p_response["message"] = "Okuma Hatası"
        return p_response

    if (reader):

        geojson = shp_to_geojson(reader)
        p_response["status"] = 1
        p_response["message"] = "Başarılı"

        if (kwargs.get("transform") and kwargs.get("dcrs") and kwargs.get("tcrs")):
            print("dönüşüm yaılıor")
            geojson = FeatureCollection(
                tranform_geojson(features=geojson['features'], input_crs=kwargs["dcrs"], output_crs=kwargs["tcrs"]))

        if (kwargs.get("precision")):
            geojson = FeatureCollection(
                [val for val in coord_precision(geojson['features'], kwargs["precision"])])

    p_response["data"] = geojson

    return p_response


def shp_to_geojson(shp):

    fields = shp.fields[1:]
    field_names = [field[0] for field in fields]
    buffer = []
    for sr in shp.shapeRecords():
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buffer.append(dict(type="Feature",
                           geometry=geom, properties=atr))

    feature_collection = {"type": "FeatureCollection",
                          "features": buffer}

    fc = FeatureCollection(buffer)

    return fc


def ConvertKML(file, separate_folders=False,
               style_type=None, style_filename='style.json'):
    # Create absolute paths
    mylayers = []
    #kml_path = Path(kml_path).resolve()
    try:

        file.seek(0)  # go to the start of the stream

        # Parse KML

        kml_str = file.read()
        root = md.parseString(kml_str)

        # Build GeoJSON layers

        layers = build_layers(root)

        # Write layers to files
        for i in range(len(layers)):
            mylayers.append((layers[i]))
    except:
        return {"status": 0, "layers": mylayers}
    return ({"status": 1, "layers": mylayers})
