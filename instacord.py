from flask import Flask, redirect, url_for, render_template, request, session, flash, g,jsonify
from datetime import timedelta
import sqlite3, base64
from db import (
    init_db,
    #create
    create_user,
    create_post,
    #checks/lookups
    exists,
    isCorrect,
    postid_to_userid,
    get_posts,
    get_users,
    get_short_user_info,
    get_db_user_info,
    get_all_user_info,
    identify,
    get_like_count,
    is_liked,
    get_follow_count,
    is_followed,
    #changing the db
    update_info,
    delete_user,
    delete_post,
    toggle_like,
    toggle_follow,
    toggle_admin,
    comment_on_post
)

app = Flask(__name__)
app.secret_key = "m4ddiesux"
app.permanent_session_lifetime = timedelta(days = 5)

with app.app_context():
    init_db()

def log_in(userid):
    info = get_db_user_info(userid)
    session.permanent = True;
    session["userid"] = info[0]
    session["user"] = info[1]
    session["email"] = info[2]

@app.context_processor
def utility_processor():
    def selfdata():
        if "userid" in session:
            user = get_db_user_info(session["userid"])
            return [f"{user[1]}", f"{user[4]}", user[6], user[0]]
        return [None, None, None]
    return dict(selfdata=selfdata)

@app.route("/register", methods=["POST", "GET"])
def register():
    if "userid" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        user = request.form["nm"]
        email = request.form["email"]
        password = request.form["pswd"]
        if exists(user,'user'):
            return redirect(url_for("register"))
        elif exists(email,'email'):
            return redirect(url_for("register"))
        else:
            create_user(user,email,password)
            log_in(identify(user))
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
            if isCorrect(identify(user), password):
                log_in(identify(user))
                return redirect(url_for("home"))
            else:
                return redirect(url_for("login"))
        else:
            return redirect(url_for("login"))
    else:
        return render_template("login.html")

@app.route("/")
def home():
    if "userid" in session:
        posts = get_posts('*',session['userid'])
        return render_template("index.html", posts = posts)
    return redirect(url_for("login"))

@app.route("/account/<user>")
def account(user):
    if "userid" in session:
        if exists(user,'user'):
            user_info = get_all_user_info(identify(user),session['userid'])
            posts = get_posts(user_info[0][0],session["userid"])
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
        return redirect(url_for('account',user = session["user"]))
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
            return redirect(url_for('account',user = session["user"]))
        else:
            return redirect(url_for('password'))
    else:
        return render_template("password.html")

@app.route("/email", methods=["POST", "GET"])
def email():
    if "userid" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        email = request.form["email"]
        if exists(email,'email'):
            return redirect(url_for('email'))
        else:
            session["email"] = email
            update_info(session["userid"],request.form["email"],'email')
            return redirect(url_for('account',user = session["user"]))
    else:
        return render_template("email.html")

@app.route("/username", methods=["POST", "GET"])
def username():
    if "userid" not in session:
        return redirect(url_for("logout"))
    if request.method == "POST":
        user = request.form["username"]
        if exists(user,'user'):
            return redirect(url_for('username'))
        else:
            update_info(session["userid"],request.form["username"],'username')
            session["user"] = user
            return redirect(url_for('account',user = session["user"]))
    else:
        return render_template("username.html")

@app.route("/delete")
def delete():
    if 'userid' in session:
        if exists(session['user'],'user'):
            delete_user(session['userid'])
    return redirect(url_for("logout"))

@app.route("/like/<postid>", methods=["POST"])
def like(postid):
    if 'userid' in session:
        toggle_like(postid,session['userid'])
        count = get_like_count(postid)
        liked = is_liked(postid,session["userid"])
        return jsonify({"count": count, "liked": liked})
    return redirect(url_for('home'))

@app.route("/follow/<userid>", methods=["POST"])
def follow(userid):
    if 'userid' in session:
        toggle_follow(userid,session['userid'])
        count = get_follow_count(userid)
        followed = is_followed(userid,session["userid"])
        return jsonify({"count": count, "followed": followed})
    return redirect(url_for('home'))

@app.route("/delete/<postid>", methods=["POST"])
def deletepost(postid):
    if "userid" in session:
        if session["userid"] == postid_to_userid(postid):
            delete_post(postid)
            return jsonify({"error": "Unauthorized"}), 403
    return

@app.route("/deleteuser/<int:userid>", methods=["POST"])
def deleteuser(userid):
    if "userid" in session:
        curuser = session["userid"]
        authority = curuser == 0 and userid != 0
        authority |= (get_db_user_info(curuser)[6] == 1 and get_db_user_info(userid)[6] == 0)
        if authority:
            delete_user(userid)
            return ""
    return jsonify({"error": "Unauthorized"}), 403

@app.route("/comment/<postid>", methods=["POST"])
def comment(postid):
    if "userid" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    contents = data.get("comment", "").strip()
    commentid = comment_on_post(postid, session['userid'], contents)
    return jsonify({"commentid": commentid})

@app.route("/owner")
def owner():
    if "user" not in session:
        return redirect(url_for("login"))
    elif session["userid"] == 0:
        return render_template("owner.html")
    else:
        return redirect(url_for("home"))

@app.route("/userlist")
def userlist():
    if "user" not in session:
        return redirect(url_for("login"))
    users = get_users()
    self = get_db_user_info(session["userid"])
    return render_template("userlist.html", users = users)

@app.route("/adminuser/<int:userid>", methods=["POST"])
def adminuser(userid):
    if "userid" in session:
        if session["userid"] == 0 and userid != 0:
            toggle_admin(userid)
            admin = get_db_user_info(userid)[6]
            taginfo = get_short_user_info(userid)[2]
            color = taginfo[1]
            name = taginfo[0]
            return jsonify({"admin": admin, "color": color, "name": name})
    return jsonify({"error": "Unauthorized"}), 403

if __name__ == "__main__":
    app.run(debug = True)