from flask import Flask, redirect, url_for, render_template, request, session, flash, g,jsonify
from datetime import timedelta
import sqlite3, base64
from db import (
    init_db,
    create_user,
    exists,
    isCorrect,
    create_post,
    get_posts,
    get_user_info,
    update_info,
    delete_user,
    toggle_like,
    toggle_follow,
    check_likes,
    check_follows,
    delete_post,
    identify,
    postid_to_userid
)

app = Flask(__name__)
app.secret_key = "m4ddiesux"
app.permanent_session_lifetime = timedelta(days = 5)

with app.app_context():
    init_db()

def log_in(userid):
    info = get_user_info(userid,userid)
    session.permanent = True;
    session["userid"] = info[0]
    session["user"] = info[1]
    session["email"] = info[2]

@app.route("/register", methods=["POST", "GET"])
def register():
    if "userid" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        user = request.form["nm"]
        email = request.form["email"]
        password = request.form["pswd"]
        if exists(user,'user'):
            flash("Register Unsuccesful: User Exists", "info")
            return redirect(url_for("register"))
        elif exists(email,'eml'):
            flash("Register Unsuccesful: Email Exists", "info")
            return redirect(url_for("register"))
        else:
            create_user(user,email,password)
            log_in(identify(user))
            flash("Register Succesful!", "info")
            return redirect(url_for("avatar"))
    else:
        return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if "userid" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        user = request.form["nm"]
        password = request.form["pswd"]
        if exists(user,'user'):
            if isCorrect(user, password):
                log_in(identify(user))
                flash("Login Succesful!", "info")
                return redirect(url_for("home"))
            else:
                flash("Login Unsuccesful: Password is Wrong", "info")
                return redirect(url_for("login"))
        else:
            flash("Login Unsuccesful : Username not found.", "info")
            return redirect(url_for("login"))
    else:
        return render_template("login.html")

@app.route("/")
def home():
    if "userid" in session:
        posts = get_posts('*',session['userid'])
        return render_template("index.html", posts = posts)
    return redirect(url_for("login"))

@app.route("/account")
def accsearch():
    if "userid" in session:
        return redirect(url_for("account", user = session["user"]))  
    return redirect(url_for("login"))

@app.route("/account/<user>")
def account(user):
    if "userid" in session:
        if exists(user,'user'):
            user_info = get_user_info(identify(user),session['userid'])
            posts = get_posts(user_info[0],session["userid"])
            if session["userid"] == identify(user):
                return render_template("self.html", info = user_info, posts = posts)
            return render_template("account.html", info = user_info, posts = posts)
        else: 
            return "<h1> User Doesn't Exist!<h2>"
    return redirect(url_for("login"))

@app.route("/post", methods=["POST", "GET"])
def post():
    if "userid" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        mmnt = request.files["moment"]
        if mmnt and mmnt.filename != '':
            encd_bytes = base64.b64encode(mmnt.read()).decode('utf-8')
            data_uri = f"data:{mmnt.mimetype};base64,{encd_bytes}"
        capt = request.form["caption"]
        userid = session["userid"]
        create_post(data_uri,capt,userid)
        return redirect(url_for("home"))
    else:
        return render_template("post.html")

@app.route("/logout")
def logout():
    if "userid" in session:
        session.pop("user", None)
        session.pop("email", None)
        session.pop("userid", None)
        flash("You have been logged out!", "info")
    return redirect(url_for("login"))

@app.route("/avatar", methods=["POST","GET"])
def avatar():
    if "userid" not in session:
        return redirect(url_for("login"))   
    if request.method == "POST":
        avatar = request.files["avatar"]
        if avatar and avatar.filename != '':
            encd_bytes = base64.b64encode(avatar.read()).decode('utf-8')
            data_uri = f"data:{avatar.mimetype};base64,{encd_bytes}"
        userid = session["userid"]
        update_info(userid, data_uri, 'avatar')
        return redirect(url_for('accsearch'))
    else:
        return render_template("avatar.html")
    
@app.route("/password", methods=["POST", "GET"])
def password():
    if "userid" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        passold = request.form["passwordold"]
        passnew = request.form["passwordnew"]
        userid = session["userid"]
        if isCorrect(userid,passold):
            update_info(userid,passnew,'password')
            return redirect(url_for('accsearch'))
        else:
            flash("Old Password is wrong!", "info")
            return redirect(url_for('password'))
    else:
        return render_template("password.html")

@app.route("/email", methods=["POST", "GET"])
def email():
    if "userid" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        email = request.form["email"]
        if exists(email,'eml'):
            flash("Email Exists!", "info")
            return redirect(url_for('email'))
        else:
            session["email"] = email
            update_info(session["userid"],request.form["email"],'email')
            return redirect(url_for('accsearch'))
    else:
        return render_template("email.html")

@app.route("/username", methods=["POST", "GET"])
def username():
    if "userid" not in session:
        return redirect(url_for("logout"))
    if request.method == "POST":
        user = request.form["username"]
        if exists(user,'user'):
            flash("Username Exists!", "info")
            return redirect(url_for('username'))
        else:
            update_info(session["userid"],request.form["username"],'username')
            session["user"] = user
            return redirect(url_for('accsearch'))
    else:
        return render_template("username.html")

@app.route("/delete")
def delete():
    if 'user' in session:
        if exists(session['user'],'user'):
            delete_user(session['userid'])
    return redirect(url_for("logout"))

@app.route("/like/<postid>", methods=["POST"])
def like(postid):
    if 'user' in session:
        toggle_like(postid,session['userid'])
        count, liked = check_likes(postid, session["userid"])
        return jsonify({"count": count, "liked": liked})
    return redirect(url_for('home'))

@app.route("/follow/<userid>", methods=["POST"])
def follow(userid):
    if 'user' in session:
        toggle_follow(userid,session['userid'])
        count, followed = check_follows(userid, session["userid"])
        return jsonify({"count": count, "followed": followed})
    return redirect(url_for('home'))

@app.route("/delete/<postid>", methods=["POST"])
def deletepost(postid):
    if "userid" in session:
        if session["userid"] == postid_to_userid(postid):
            delete_post(postid)
            return "", 204
    return

if __name__ == "__main__":
    app.run(debug = True)