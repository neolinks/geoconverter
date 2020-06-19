import flask
import requests
import json
import itertools
import os
import zipfile
import shapefile

from flask import Flask, render_template, request, redirect, abort, flash, url_for, jsonify, request, make_response
from werkzeug.utils import secure_filename
from werkzeug._compat import BytesIO
from prc2 import import_data, checkExtension
import io
from tempfile import SpooledTemporaryFile

app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/main', methods=['POST'])
def getgeojson():

    if request.method == 'POST':
        print(request.args.to_dict())

        # formdan dosya gelip gelmediğini kontrol edelim
        if 'file' not in request.files:
            print("Dosya yüklenmedi")
            #app.make_response(('Dosya yüklenmedi', 403))
            return "Dosya yüklenmedi", 400, {'ContentType': 'text/html'}

        # kullanıcı dosya seçmemiş ve tarayıcı boş isim göndermiş mi
        file = request.files.get('file')

        precision = request.args.get('precision')

        if file.filename == '':

            app.make_response(('Dosya yüklenmedi', 403))
            return "Dosya yüklenmedi", 403, {'ContentType': 'text/html'}
        # gelen dosyayı güvenlik önlemlerinden geçir
        if file and checkExtension(file.filename):
            filename = secure_filename(file.filename)
            #memoryshape = (file.getvalue())

            zipped = filename
            zf = zipfile.ZipFile(file)

            file_like_object = file.stream._file
            zipfile_ob = zipfile.ZipFile(file_like_object)
            print(zipfile_ob.namelist())

            shpname, shxname, dbfname, prjname = zipfile_ob.namelist()
            cloudshp = StringIO(zipfile_ob.read(shpname))
            cloudshx = StringIO(zipfile_ob.read(shxname))
            clouddbf = StringIO(zipfile_ob.read(dbfname))
            r = shapefile.Reader(shp=cloudshp, shx=cloudshx, dbf=clouddbf)
            print(r.bbox)

            file_names = zipfile_ob.namelist()
            print(file_names)
            for item in zipfile_ob.filelist:
                pass
                # print(item)

            """ with open(zipfile_ob, 'rb') as file_data:
                bytes_content = file_data.read() """

            new_zip = BytesIO()

            with zipfile.ZipFile(new_zip, 'w') as new_archive:
                for item in zipfile_ob.filelist:
                    # If you spot an existing file, create a new object

                    new_archive.writestr(item, zipfile_ob.read(item.filename))

            """ with open(zipped, 'rb') as file_data:
                bytes_content = file_data.read() """

            #reader = import_data(file.read())
            reader = import_data(file.getvalue())
            fields = reader.fields[1:]
            field_names = [field[0] for field in fields]

            print(field_names)
            buffer = []
            for sr in reader.shapeRecords():
                atr = dict(zip(field_names, sr.record))
                geom = sr.shape.__geo_interface__
                buffer.append(dict(type="Feature",
                                   geometry=geom, properties=atr))

            feature_collection = {"type": "FeatureCollection",
                                  "features": buffer}

            return jsonify(feature_collection), 200, {'ContentType': 'application/json'}

        else:
            return "Hata", 500

    else:
        abort(401)


if __name__ == '__main__':
    app.run(debug=True)
