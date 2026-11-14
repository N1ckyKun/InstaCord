from flask import Flask, redirect, url_for, render_template, request, session, flash, g
from datetime import timedelta
import sqlite3, base64
from db import (
    init_db,
    insert_user,
    it_exists,
    compare_pswd,
    create_post,
    get_posts,
    get_user_info,
    get_posts_from_user,
    update_info,
    delete_user
)

app = Flask(__name__)
app.secret_key = "m4ddiesux"
app.permanent_session_lifetime = timedelta(days = 5)

with app.app_context():
    init_db()

def log_in(username):
    info = get_user_info(username)
    session["userid"] = info[0]
    session["user"] = info[1]
    session["email"] = info[2]

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        if "user" in session:
            return redirect(url_for("home"))
        return render_template("register.html")
    else:
        user = request.form["nm"]
        email = request.form["email"]
        password = request.form["pswd"]
        if it_exists(user,'usr'):
            flash("Register Unsuccesful: User Exists", "info")
            return redirect(url_for("register"))
        elif it_exists(email,'eml'):
            flash("Register Unsuccesful: Email Exists", "info")
            return redirect(url_for("register"))
        else:
            insert_user(user,email,password)
            log_in(user)
            flash("Register Succesful!", "info")
            return redirect(url_for("avatar"))
    
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if "user" in session:
            return redirect(url_for("home"))
        return render_template("login.html")
    else:
        user = request.form["nm"]
        password = request.form["pswd"]
        if it_exists(user,'usr'):
            if compare_pswd(user, password):
                log_in(user)
                flash("Login Succesful!", "info")
                return redirect(url_for("home"))
            else:
                flash("Login Unsuccesful: Password is Wrong", "info")
                return redirect(url_for("login"))
        else:
            flash("Login Unsuccesful : Username not found.", "info")
            return render_template("login.html")

@app.route("/")
def home():
    if "user" in session:
        if it_exists(session['user'],"usr"):
            posts = get_posts()
            return render_template("index.html", posts = posts)
    return redirect(url_for("logout"))

@app.route("/account")
def accsearch():
    if "user" in session:
        return redirect(url_for("account", user = session["user"]))
    else:
        return redirect(url_for("login"))

@app.route("/account/<user>")
def account(user):
    if it_exists(user,'usr'):
        user_info = get_user_info(user)
        posts = get_posts_from_user(user_info[0])
        if session["user"] == user:
            return render_template("self.html", info = user_info, posts = posts)
        return render_template("account.html", info = user_info, posts = posts)
    else: 
        return "<h1> User Doesn't Exist!<h2>"

@app.route("/post", methods=["POST", "GET"])
def post():
    if request.method == "GET":
        if "user" in session:
            return render_template("post.html")
        else:
            return redirect(url_for("login"))
    else:
        mmnt = request.files["moment"]
        if mmnt and mmnt.filename != '':
            encd_bytes = base64.b64encode(mmnt.read()).decode('utf-8')
            data_uri = f"data:{mmnt.mimetype};base64,{encd_bytes}"
        capt = request.form["caption"]
        dscrpt = request.form["description"]
        userid = session["userid"]
        create_post(data_uri,capt,dscrpt,userid)
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user", None)
        session.pop("email", None)
        flash("You have been logged out!", "info")
    return redirect(url_for("login"))

@app.route("/avatar", methods=["POST","GET"])
def avatar():
    if request.method == "GET":
        if "user" in session:
            if it_exists(session['user'],'usr'):
                return render_template("avatar.html")
            return redirect(url_for("logout"))
    else:
        avatar = request.files["avatar"]
        if avatar and avatar.filename != '':
            encd_bytes = base64.b64encode(avatar.read()).decode('utf-8')
            data_uri = f"data:{avatar.mimetype};base64,{encd_bytes}"
        user = session["user"]
        update_info(user, data_uri, 'avatar')
        return redirect(url_for("home"))
    
@app.route("/password", methods=["POST", "GET"])
def password():
    if request.method == "GET":
        if "user" in session:
            if it_exists(session['user'],'usr'):
                return render_template("password.html")
            return redirect(url_for("logout"))
    else:
        passold = request.form["passwordold"]
        if compare_pswd(session["user"],passold):
            update_info(session["user"],request.form["passwordnew"],'password')
            return redirect(url_for('home'))
        else:
            flash("Old Password is wrong!", "info")
            return redirect(url_for('password'))

@app.route("/email", methods=["POST", "GET"])
def email():
    if request.method == "GET":
        if "user" in session:
            if it_exists(session['user'],'usr'):
                return render_template("email.html")
            return redirect(url_for("logout"))
    else:
        email = request.form["email"]
        if it_exists(email,'eml'):
            flash("Email Exists!", "info")
            return redirect(url_for('email'))
        else:
            update_info(session["user"],request.form["email"],'email')
            return redirect(url_for('home'))

@app.route("/username", methods=["POST", "GET"])
def username():
    if request.method == "GET":
        if "user" in session:
            if it_exists(session['user'],'usr'):
                return render_template("username.html")
            return redirect(url_for("logout"))
    else:
        user = request.form["username"]
        if it_exists(user,'usr'):
            flash("Username Exists!", "info")
            return redirect(url_for('username'))
        else:
            update_info(session["user"],request.form["username"],'username')
            session["user"] = user
            return redirect(url_for('home'))

@app.route("/delete")
def delete():
    if 'user' in session:
        if it_exists(session['user'],'usr'):
            delete_user(session['user'])
    return redirect(url_for("logout"))

if __name__ == "__main__":
    app.run(debug = True)