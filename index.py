from datetime import timedelta
from flask import Flask, flash, session, request, redirect, url_for, render_template, send_from_directory
from flask_googlestorage import GoogleStorage, Bucket
from werkzeug.utils import secure_filename
from google.cloud import storage

import os

files = Bucket("files")
storage = GoogleStorage(files)

app = Flask(__name__)

app.config.update(
    GOOGLE_STORAGE_LOCAL_DEST = app.instance_path,
    GOOGLE_STORAGE_SIGNATURE = {"expiration": timedelta(minutes=5)},
    GOOGLE_STORAGE_FILES_BUCKET = "splittymon.appspot.com"
)

# configure upload folder
upload_folder = './tmp/uploads'
app.config['UPLOAD_FOLDER'] = upload_folder

# configure stems folder
stems_folder = './tmp/stems'
app.config['STEMS_FOLDER'] = stems_folder

storage.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        # check if the post request has a file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # if file exists then assign it to variable
        file = request.files['file']

        # check if the file has an empty name
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # if file exists and name checks out
        # start separation process
        if file and allowed_file(file.filename):

            # safely assign filename
            filename = secure_filename(file.filename)

            # save file to the uploads folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # separate stems
            separate(filename)

            # create and return zip file
            create_zip(filename)
            zip_filepath = return_file(filename)

            relative_fp = "/download/" + zip_filepath

            return render_template("download.html", filename=relative_fp, zipfile_name=zip_filepath)
    else:
        return render_template("index.html")

def allowed_file(filename):
    allowed_extensions = {'mp3', 'wav'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def separate(filename):
    from spleeter.separator import Separator
    separator = Separator('spleeter:2stems')

    separator.separate_to_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), os.path.join(app.config['STEMS_FOLDER']))

    return None

def return_file(filename):

    split_filename = filename.split('.')
    file_name = split_filename[0]
    path = file_name + ".zip"
    return path

def create_zip(filename):
    from zipfile import ZipFile

    split_filename = filename.split('.')
    file_name = split_filename[0]
    zipfile_name = "./tmp/stems/" + file_name + ".zip"

    vocals_path = './tmp/stems/' + file_name + '/vocals.wav'
    instr_path = './tmp/stems/' + file_name + '/accompaniment.wav'

    zip_obj = ZipFile(zipfile_name, 'w')
    zip_obj.write(vocals_path)
    zip_obj.write(instr_path)

    zip_obj.close()

@app.route('/download/<filename>')
def download(filename):
    print("hereeeee")
    print(filename)
    return send_from_directory('./tmp/stems/', filename, as_attachment=True)

@app.route('/pro', methods=['GET', 'POST'])
def pro():
    if request.method == 'POST':
        # email = request.form.get('email')
        # message = request.form.get('message')
        #
        # filename_to_feedback_db = Feedback(email=email, message=message)
        #
        # db.session.add(filename_to_feedback_db)
        # db.session.commit()

        return render_template("pro.html")
    else:
        return render_template("pro.html")
