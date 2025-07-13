import os
from flask import Flask, request

app = Flask(__name__)

UPLOAD_FOLDER = "/home/ec2-user/received_logs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    return f"✅ File {file.filename} uploaded successfully!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)