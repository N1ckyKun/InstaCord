from flask import Flask, redirect, url_for, render_template, request, session, flash, g,jsonify
from datetime import timedelta
import sqlite3, base64, os, uuid
from PIL import Image, UnidentifiedImageError
from db import (
    init_db,
    #create
    create_user,
    create_post,
    create_report,
    #checks/lookups
    exists,
    isCorrect,
    postid_to_userid,
    comid_to_userid,
    comid_to_postid,
    delete_comment,
    get_posts,
    get_users,
    get_short_user_info,
    get_db_user_info,
    get_all_user_info,
    get_post_comment_count,
    identify,
    get_reports,
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
    comment_on_post,
    get_db
)

app = Flask(__name__)
app.secret_key = "m4ddiesux"
app.permanent_session_lifetime = timedelta(days = 5)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
upfolder = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(upfolder, exist_ok=True)

with app.app_context():
    init_db()
    g.db = get_db()

def validate_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    try:
        img = Image.open(file_storage)
        allowed = {'JPEG','PNG','WEBP'}
        if img.format not in allowed:
            return None
        img.verify()
        file_storage.seek(0)
        img = Image.open(file_storage)
        unique_filename = f'{uuid.uuid4().hex}.webp'
        save_path = os.path.join(upfolder, unique_filename)
        img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
        img.save(save_path, format='WEBP', quality=80, method=6, optimize=True)
        return f'/static/uploads/{unique_filename}'
    except (UnidentifiedImageError, OSError, SyntaxError):
        return None

def send_log(validity):
    if validity == "Login":
        return url_for("login")
    return url_for("logout")

def check_validity():
    validity = [0, "Login"]
    if "userid" in session:
        validity = [0, "Logout"]
        if exists(session["userid"], "id"):
            validity = [1, "User"]
            if get_db_user_info(session["userid"])[6] == 1:
                validity = [1, "Admin"]
            if session["userid"] == 0:
                validity = [1, "Owner"]
    return validity

def log_in(userid):
    info = get_db_user_info(userid)
    session.permanent = True;
    session["userid"] = userid
    session["user"] = info[1]
    session["email"] = info[2]

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.context_processor
def utility_processor():
    def selfdata():
        validity = check_validity()
        if validity[0]:
            self = []
            user = get_db_user_info(session["userid"])
            for i in user:
                self.append(i)
            return self
        return [0,0,0,0,0,0,0,0]    
    return dict(selfdata=selfdata)

@app.route("/register", methods=["POST", "GET"])
def register():
    if "userid" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        user = request.form["nm"].strip()
        email = request.form["email"].lower().strip()
        password = request.form["pswd"].strip()
        if exists(user,'user') or user == '':
            return redirect(url_for("register"))
        elif exists(email,'email') or email == '':
            return redirect(url_for("register"))
        elif password == '':
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
        user = request.form["nm"].strip()
        password = request.form["pswd"].strip()
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
    validity = check_validity()
    if validity[0]:
        posts = get_posts('*',session['userid'])
        return render_template("index.html", posts = posts)
    return redirect(send_log(validity[1]))

@app.route("/account/<user>")
def account(user):
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if exists(user,'user'):
        user_info = get_all_user_info(identify(user),session['userid'])
        posts = get_posts(user_info[0][0],session["userid"])
        return render_template("account.html", info = user_info, posts = posts)
    else: 
        return "<h1> User Doesn't Exist!<h2>"
    

@app.route("/post", methods=["POST", "GET"])
def post():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if request.method == "POST":
        mmnt = request.files["moment"]
        mmnt = validate_image(mmnt)
        if not mmnt:
            return redirect(url_for("post"))
        capt = request.form["caption"]
        userid = session["userid"]
        create_post(mmnt,capt,userid)
        return redirect(url_for("home"))
    else:
        shortinfo = get_short_user_info(session["userid"])
        return render_template("post.html", shortinfo = shortinfo)

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("email", None)
    session.pop("userid", None)
    return redirect(url_for("login"))

@app.route("/avatar", methods=["POST","GET"])
def avatar():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if request.method == "POST":
        avatar = request.files["avatar"]
        avatar = validate_image(avatar)
        if not avatar:
            return redirect(url_for("avatar"))
        userid = session["userid"]
        update_info(userid, avatar, 'avatar')
        return redirect(url_for('account',user = session["user"]))
    else:
        return render_template("avatar.html")
    
@app.route("/password", methods=["POST", "GET"])
def password():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if request.method == "POST":
        passold = request.form["passwordold"].strip()
        passnew = request.form["passwordnew"].strip()
        userid = session["userid"]
        if (not isCorrect(userid,passold)) or passnew == "":
            return redirect(url_for('password'))
        update_info(userid,passnew,'password')
        return redirect(url_for('account',user = session["user"]))
        
    else:
        return render_template("password.html")

@app.route("/email", methods=["POST", "GET"])
def email():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        if exists(email,'email') or email == "":
            return redirect(url_for('email'))
        else:
            session["email"] = email
            update_info(session["userid"],email,'email')
            return redirect(url_for('account',user = session["user"]))
    else:
        return render_template("email.html")

@app.route("/username", methods=["POST", "GET"])
def username():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if request.method == "POST":
        user = request.form["username"].strip()
        if exists(user,'user') or user == "":
            return redirect(url_for('username'))
        else:
            update_info(session["userid"],user,'username')
            session["user"] = user
            return redirect(url_for('account',user = session["user"]))
    else:
        return render_template("username.html")

@app.route("/delete", methods=["POST"])
def delete():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    delete_user(session['userid'])
    return redirect(url_for("logout"))

@app.route("/like/<int:postid>", methods=["POST"])
def like(postid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(postid, "postid"):
        return jsonify({"error": "Not Exist"}), 403
    toggle_like(postid,session['userid'])
    count = get_like_count(postid)
    liked = is_liked(postid,session["userid"])
    return jsonify({"count": count, "liked": liked})

@app.route("/follow/<int:userid>", methods=["POST"])
def follow(userid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(userid, "id"):
        return jsonify({"error": "Not Exist"}), 403
    if userid == session["userid"]:
        return jsonify({"error": "Self"}), 403
    toggle_follow(userid,session['userid'])
    count = get_follow_count(userid)
    followed = is_followed(userid,session["userid"])
    return jsonify({"count": count, "followed": followed})

@app.route("/delete/<int:postid>", methods=["POST"])
def deletepost(postid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(postid, "postid"):
        return jsonify({"error": "Not Exist"}), 403
    if session["userid"] == postid_to_userid(postid) or get_db_user_info(session["userid"])[6] == 1:
        delete_post(postid)
        return ""
    return jsonify({"error": "Unauthorized"}), 403

@app.route("/deleteuser/<int:userid>", methods=["POST"])
def deleteuser(userid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(userid, "id"):
            return jsonify({"error": "Not Exist"}), 403
    curuser = session["userid"]
    authority = (curuser == 0 and userid != 0)
    authority |= (get_db_user_info(curuser)[6] == 1 and get_db_user_info(userid)[6] == 0)
    authority &= (curuser != userid)
    if authority:
        delete_user(userid)
        return ""
    return jsonify({"error": "Unauthorized"}), 403

@app.route("/comment/<int:postid>", methods=["POST"])
def comment(postid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(postid, "postid"):
        return jsonify({"error": "Not Exist"}), 403
    data = request.get_json()
    contents = data.get("comment", "").strip()
    if contents != "":
        commentid = comment_on_post(postid, session['userid'], contents)
        return jsonify({"commentid": commentid})
    return jsonify({"error": "Empty Comment"}), 403

@app.route("/owner")
def owner():
    if "user" in session and session["userid"] == 0:
        return render_template("owner.html")
    return redirect(url_for("home"))

@app.route("/userlist")
def userlist():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    users = get_users()
    return render_template("userlist.html", users = users)

@app.route("/reports")
def reports():
    validity = check_validity()
    if not validity[0]:
        return redirect(send_log(validity[1]))
    if validity[1] == "User":
        return redirect(url_for("home"))
    reports = get_reports()
    return render_template("reports.html", reports = reports)

@app.route("/adminuser/<int:userid>", methods=["POST"])
def adminuser(userid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(userid, "id"):
        return jsonify({"error": "Not Exist"}), 403
    if session["userid"] == 0 and userid != 0:
        toggle_admin(userid)
        admin = get_db_user_info(userid)[6]
        taginfo = get_short_user_info(userid)[2]
        color = taginfo[1]
        name = taginfo[0]
        return jsonify({"admin": admin, "color": color, "name": name})
    return jsonify({"error": "Unauthorized"}), 403

@app.route("/report/<int:userid>", methods=["POST","GET"])
def report(userid):
    validity = check_validity()
    if not validity[0] or (not exists(userid,"id")):
        return redirect(url_for("home"))
    shortinfo = get_short_user_info(userid)
    if request.method == "POST":
        reason=request.form.get("reason")
        details=request.form.get("details")
        create_report(reason,details,userid)
        return(redirect(url_for("account", user = shortinfo[0])))
    else:
        return render_template("report.html", shortinfo = shortinfo)
        
@app.route("/deletecom/<int:comid>", methods=["POST"])
def deletecom(comid):
    validity = check_validity()
    if not validity[0]:
        return jsonify({"error": "Unauthorized"}), 403
    if not exists(comid, "comid"):
        return jsonify({"error": "Not Exist"}), 403
    if session["userid"] == comid_to_userid(comid) or get_db_user_info(session["userid"])[6] == 1:
        postid = comid_to_postid(comid)
        delete_comment(comid)
        count = get_post_comment_count(postid)
        return jsonify({"count": count})
    return jsonify({"error": "Unauthorized"}), 403
    
if __name__ == "__main__":
    app.run(debug = True)