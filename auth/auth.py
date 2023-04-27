import os
from flask import request,render_template,redirect,url_for,session, flash,Blueprint
from replit import db
from datetime import datetime
import hashlib
app = Blueprint('auth', __name__)
now = datetime.now()

def check_login():
    try:name=session["user"]["name"]
    except:name=""
    if name not in db.keys():
        session["access"]="False"
        return False
    elif int(now.strftime("%d%H%M"))+30<=int(session["user"]["time"]):
        session["access"]="False"
        return False
    else:
        session["access"]="True"
        return True
def set_time():
    session["user"]["time"]=now.strftime("%d%H%M")

app.secret_key = os.environ['secret']
open_list=["/","/login","/signup","/wipedb"]

@app.before_request 
def before_request_callback(): 
    if not check_login():
        path=request.path
        if path not in open_list:
            flash("Session is over")
            return redirect(url_for('auth.login'))
        else:
            session["access"]="False"
    else: 
        set_time()
    
@app.route("/login")
def login():
    if session["access"]=="True":
        return redirect(url_for('index'))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def loginPOST():
    data = request.form
    name=data["name"]
    
    password=hashlib.sha256(data["password"].encode("utf-8")).hexdigest()
    if name in db.keys():
        if password==db[name]["password"]:
            session["user"]={"name":data["name"],"time":now.strftime("%d%H%M"),"power":db[name]["power"]}
            session["access"]="True"
            print({"name":data["name"],"time":now.strftime("%d%H%M"),"power":db[name]["power"]})
            return redirect(url_for('index'))
        else:
            flash("wrong username/password")
            return redirect(url_for('auth.login'))
    else:
        flash("wrong username/password")
        return redirect(url_for('auth.login'))
            
@app.route("/profile")
def profile():
    print(session["user"]["power"])
    return render_template("profile.html",access=session["access"])
    
@app.route("/signup")
def signup():
    return render_template("signup.html",access=session["access"])
    
@app.route("/signup", methods=["POST"])
def signupPOST():
    data = request.form
    if data["name"] not in db:
        session["user"]={"name":data["name"],"time":now.strftime("%d%H%M"),"power":"1"}
        db[data["name"]]={"password":hashlib.sha256(data["password"].encode("utf-8")).hexdigest(),"power":1}
        session["access"]="True"
        return redirect(url_for('index'))
    else:
        flash("Username in use")
        return redirect(url_for('auth.signup'))

@app.route("/signout")
def signout():
    session["user"]=""
    session["access"]="False"
    return redirect("/")

@app.route("/change_password", methods=["POST"])
def change_password():
    data = request.form
    if hashlib.sha256(data["old-password"].encode("utf-8")).hexdigest()==db[session["user"]["name"]]["password"]:     
        if data["new-password"]!="":
            newPassword=hashlib.sha256(data["new-password"].encode("utf-8")).hexdigest()
            
            db[session["user"]["name"]]["password"]=newPassword
            flash("password changed")
        else:
            flash("old password entered is incorrectly entered")
    else:
        flash("previous password is wrong")
    return redirect(url_for('auth.profile'))

@app.route("/wipedb", methods=["GET"])
def wipe():
    for x in db.keys():
        del db[x]
    return redirect("/")