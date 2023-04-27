from flask import Flask, request, render_template, redirect, url_for, send_file, flash , session
import os
import uuid
from datetime import datetime
import json
app = Flask(__name__)
app.secret_key = os.environ['secret_key']

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'json', 'css', 'mp4', 'avi', 'html'}

def read_json_user():
    try:
        with open("users/"+ session["user"]["name"]+".json", 'r') as f:
            return json.load(f)
    except:
        with open("users/"+session["user"]["name"]+".json", 'w') as f:
            return {}

def write_json_user(id,name):
    jsons=read_json_user()
    with open("users/"+ session["user"]["name"]+".json", 'w') as f:
        jsons[id]=name
        json.dump(jsons,f)
        f.close()

def read_file_list():
    try:
        with open("files.json", 'r') as f:
            return json.load(f)
    except:
        with open("files.json", 'w') as f:
            return {}

def check_session():
    try:
        x=session["access"]
    except KeyError:
        session["access"]="False"

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return redirect(request.url)
        if not allowed_file(file.filename):
            return redirect(request.url)
        unique_id = str(uuid.uuid4())
        name = "files/"
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{unique_id}.{file_ext}"
        os.makedirs(name, exist_ok=True)
        file_path = os.path.join(name, filename)
        file.save(file_path)
        x=read_file_list()
        x[unique_id]={"path": file_path,"name":file.filename,"owner":session["user"]["name"]}
        with open('files.json', 'w') as files:
            json.dump(x, files)
            files.close()
        permalink = url_for('display_file', unique_id=unique_id, _external=True)
        formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user=session["user"]["name"]
        log_data = f"{formatted_time} {user} {unique_id} {file_path}"
        with open('access.log', 'a') as log_file:
            log_file.write(log_data + '\n')
        write_json_user(unique_id,file.filename)
        return redirect(permalink)   
    return render_template('upload.html',access=session["access"])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
@app.route("/")
def index():
    check_session()
    if session["access"] == "True":
        return render_template("index.html",name=session["user"]["name"],access=session["access"])
    else:
        session["user"]=""
        session["access"]="false"
        return render_template("index.html",name="",access="False")

@app.route('/display/<unique_id>')
def display_file(unique_id):
    try:
        with open('files.json', 'r') as f:
            file_data=json.load(f)
            file_path=file_data[unique_id]["path"]
            file_name=file_data[unique_id]["name"]
            file_extension = file_path.rsplit('.', 1)[1].lower()
            creation_time = os.path.getctime(file_path)
            formatted_time = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            if file_extension in {'png', 'jpg', 'jpeg', 'gif'}:
                return render_template('display_image.html', image_path=url_for('serve_file', filename=file_path), formatted_time=formatted_time,file_name=file_name, access=session["access"])
            elif file_extension == 'pdf':
                return render_template('display_pdf.html', pdf_path=url_for('serve_file', filename=file_path), formatted_time=formatted_time,file_name=file_name, access=session["access"])
            elif file_extension in {'doc', 'docx'}:
                return render_template('display_word.html', word_path=url_for('serve_file', filename=file_path), formatted_time=formatted_time, file_name=file_name,access=session["access"])
            elif file_extension == 'txt':
                with open(file_path, 'r') as text_file:
                    text = text_file.read()
                return render_template('display_text.html', text=text, formatted_time=formatted_time,file_name=file_name, access=session["access"])
            elif file_extension == 'json':
                with open(file_path, 'r') as json_file:
                    json_data = json.load(json_file)
                return render_template('display_json.html', json=json_data, formatted_time=formatted_time,file_name=file_name, access=session["access"])
            elif file_extension == 'css':
                with open(file_path, 'r') as css_file:
                    css = css_file.read()
                return render_template('display_css.html', css=css, formatted_time=formatted_time,file_name=file_name, access=session["access"])
            elif file_extension in {'mp4', 'avi'}:
                return render_template('display_video.html', video_path=url_for('serve_file', filename=file_path), formatted_time=formatted_time,file_name=file_name, access=session["access"])
            else:
                return redirect(url_for('uploads'))
    except:
        pass
    flash("image no longer exists")
    return redirect(url_for('upload_file'))

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_file(filename)
        
@app.route('/uploads')
def user_uploads():
    if session["access"]!="True":
        flash("No access")
        return redirect(url_for('auth.login'))
    try:
        x= read_json_user()
        if x:
            return render_template('uploads.html', files=x.keys(),names=x, access=session["access"])
        else:
            flash("You dont have any files")
            return render_template('uploads.html', access=session["access"])
    except FileNotFoundError:
        flash("You dont have any files")
        return render_template('uploads.html', access=session["access"])
        
@app.route('/remove/<unique_id>')
def remove_file(unique_id):
    if session["access"]!="True":
        flash("No access")
        return redirect(url_for('auth.login'))
    files=read_json_user()
    if unique_id in files:
        with open("users/"+ session["user"]["name"]+".json", 'w') as f:
            files.pop(unique_id)
            json.dump(files,f)
            f.close()
        files=read_file_list()
        os.remove(files[unique_id]["path"])
        with open("files.json", 'w') as f:
            files.pop(unique_id)
            json.dump(files,f)
            f.close()
        return redirect(url_for('user_uploads'))
    else:
        flash("No access")
        return redirect(url_for('auth.login'))
        
@app.route('/download/<unique_id>')
def download_file(unique_id):
    files=read_file_list()
    path=files[unique_id]["path"]
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return redirect(url_for('user_uploads'))

from auth.auth import app as auth
app.register_blueprint(auth)
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False)