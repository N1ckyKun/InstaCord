from flask import Flask, redirect, url_for, render_template, request, session, flash, g
from datetime import timedelta
from db import init_db, insert_user, it_exists, compare_pswd, create_post, get_posts, change_avatar, get_user_info, get_posts_from_user
import sqlite3, base64

app = Flask(__name__)
app.secret_key = "m4ddiesux"
app.permanent_session_lifetime = timedelta(days = 5)

with app.app_context():
    init_db()


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        if "user" in session:
            return redirect(url_for("home"))
        return render_template("register.html")
    else:
        usr = request.form["nm"]
        eml = request.form["email"]
        pswd = request.form["pswd"]
        if it_exists(usr,'usr'):
            flash("Register Unsuccesful: User Exists", "info")
            return redirect(url_for("register"))
        elif it_exists(eml,'eml'):
            flash("Register Unsuccesful: Email Exists", "info")
            return redirect(url_for("register"))
        else:
            insert_user(usr,eml,pswd)
            session.permanent = True
            session["user"] = usr
            flash("Register Succesful! You can also change your avatar!", "info")
            return redirect(url_for("avatar"))


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
        change_avatar(data_uri,user)
        return redirect(url_for("home"))
        

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if "user" in session:
            return redirect(url_for("home"))
        return render_template("login.html")
    else:
        usr = request.form["nm"]
        pswd = request.form["pswd"]
        if it_exists(usr,'usr'):
            if compare_pswd(usr, pswd):
                session.permanent = True
                session["user"] = request.form["nm"]
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
    return redirect(url_for("loggedout"))

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
        posts = get_posts_from_user(user)
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
        usr = session["user"]
        create_post(data_uri,capt,dscrpt,usr)
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user", None)
        session.pop("email", None)
        flash("You have been logged out!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug = True)