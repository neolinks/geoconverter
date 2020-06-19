import flask
import json
import os
import zipfile

from flask import Flask, render_template, request, redirect, abort, flash, url_for, jsonify, request, make_response
from werkzeug.utils import secure_filename
from werkzeug._compat import BytesIO
from process import import_data, checkExtension
import io
from tempfile import SpooledTemporaryFile
from io import BytesIO as StringIO
from process import ConvertKML


app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello World!"


def checkExtension(fileName):
    return '.' in fileName and \
        fileName.rsplit('.', 1)[1].lower() == "zip"


@app.route('/kml2json', methods=['POST'])
def kml_reader():
    if request.method == 'POST':
        query_params = request.args.to_dict()

        # formdan dosya gelip gelmediğini kontrol edelim
        if 'file' not in request.files:
            #app.make_response(('Dosya yüklenmedi', 403))
            return "Dosya yüklenmedi", 400, {'ContentType': 'text/html'}

        file = request.files.get('file')

        if file.filename == '':
            return "Dosya yüklenmedi", 400, {'ContentType': 'text/html'}

        if '.' not in file.filename and \
                file.filename.rsplit('.', 1)[1].lower() != "kml":
            return "Hatalı dosya", 400, {'ContentType': 'text/html'}

        filename = secure_filename(file.filename)
        file_like_object = file.stream._file

        kml_response = ConvertKML(file_like_object)
        if (kml_response["status"] == 0):
            return "Dönüşümde Hata", 400, {'ContentType': 'application/json'}

        return kml_response, 200, {'ContentType': 'application/json'}


@app.route('/main', methods=['POST'])
def getgeojson():
    required_suffixes = ["shp", "shx", "dbf", "prj"]

    if request.method == 'POST':
        query_params = request.args.to_dict()

        # formdan dosya gelip gelmediğini kontrol edelim
        if 'file' not in request.files:
            #app.make_response(('Dosya yüklenmedi', 403))
            return "Dosya yüklenmedi", 400, {'ContentType': 'text/html'}

        file = request.files.get('file')

        if file.filename == '':
            return "Dosya yüklenmedi", 400, {'ContentType': 'text/html'}

        if not zipfile.is_zipfile(file):
            return "Hatalı dosya, zip dosyası yükleyin", 400, {'ContentType': 'text/html'}

        if (file.tell()) > 1024 * 1000 * 2:
            return "Büyük dosya", 400, {'ContentType': 'text/html'}

        # gelen dosyayı güvenlik önlemlerinden geçir
        if file and checkExtension(file.filename):
            filename = secure_filename(file.filename)

            file_like_object = file.stream._file
            zipfile_ob = zipfile.ZipFile(file_like_object)

            p_response = import_data(zipfile_ob, **query_params)

            return jsonify(p_response), 400, {'ContentType': 'application/json'}

        else:
            return "Hata", 500

    else:
        abort(401)


if __name__ == '__main__':
    app.run(debug=True)
