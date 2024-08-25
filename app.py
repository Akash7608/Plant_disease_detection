#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
import os
from PIL import Image
from predict import prediction, getDataFromCSV
from werkzeug.utils import secure_filename

# from tensorflow.keras.utils import print_summary

DEVELOPMENT_ENV = os.getenv('DEVELOPMENT_ENV', 'False') == 'True'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Create image folder if not exists
if not os.path.isdir(app.config['UPLOAD_FOLDER']):
    os.mkdir(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    # Check if the file has an allowed extension
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result')
def result():
    product_id = request.args.get('id', default=-1, type=int)

    # Default fields
    app_data = {
        "disease_name": "undefined",
        "supplement name": "null",
        "supplement image": "null",
        "buy link": "null"
    }
    if product_id != -1:
        dataPredicted = getDataFromCSV(product_id)
        if any(dataPredicted):
            app_data = {
                "disease_name": dataPredicted[1],
                "supplement name": dataPredicted[2],
                "supplement image": dataPredicted[3],
                "buy link": dataPredicted[4]
            }

    return render_template('result.html', app_data=app_data)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        # Return error if no file part in request
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        # Return error if no file selected
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        pathOfFile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pathOfFile)
        try:
            product_id = prediction(pathOfFile)
        except Exception as e:
            # Return error if prediction fails
            return jsonify({'error': 'Invalid image! Kindle select Another Image.'}), 500
        finally:
            if os.path.exists(pathOfFile):
                os.remove(pathOfFile)
        return jsonify({'product_id': product_id})
    else:
        # Return error if file type is not allowed
        return jsonify({'error': 'File type not allowed'}), 400

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8001)
