import shapefile
import zipfile
import io
import os
import os.path
import tempfile
from flask import Flask
from io import BufferedReader, BytesIO


def checkExtension(fileName):
    return '.' in fileName and \
        fileName.rsplit('.', 1)[1].lower() == "zip"


def import_data(s_filename):

    fd, fname = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    f = open(fname, "wb")
    # for chunk in s_filename.read().chunks():
    f.write(s_filename)
    print(fname)
    f.close()
    if not zipfile.is_zipfile(fname):
        os.remove(fname)
        print("Geçersiz Zip arşivi.")
        return "Geçersiz Zip arşivi."

    zip = zipfile.ZipFile(fname)
    required_suffixes = [".shp", ".shx", ".dbf", ".prj"]

    has_suffix = {}
    for suffix in required_suffixes:
        has_suffix[suffix] = False
    for info in zip.infolist():
        extension = os.path.splitext(info.filename)[1].lower()
        if extension in required_suffixes:
            has_suffix[extension] = True
    for suffix in required_suffixes:
        if not has_suffix[suffix]:
            zip.close()
            os.remove(fname)
            return "Zip arşivinde "+suffix+" dosyası eksik."

    shapefile_name = None
    dst_dir = tempfile.mkdtemp()
    for info in zip.infolist():
        print(info.filename)
    for info in zip.infolist():
        if info.filename.endswith(".shp"):
            shapefile_name = info.filename

        dst_file = os.path.join(dst_dir, info.filename)

        f = open(dst_file, "wb")
        try:
            f.write(zip.read(info.filename))
        except:
            print("e")
        f.close()
    zip.close()
    print(os.path.join(dst_dir,  shapefile_name))
    r = shapefile.Reader(os.path.join(dst_dir,  shapefile_name))
    return r
