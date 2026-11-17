import sqlite3, base64, mimetypes
from flask import g, url_for 

#database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("insta.db")
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    with open("schema.sql") as schema:
        db.executescript(schema.read())

#checks
def exists(input, type):
    db = get_db()
    cursor = db.cursor()
    if type == 'user':
        chsch = "SELECT 1 FROM users WHERE username = ?"
    elif type == 'email':
        chsch = "SELECT 1 FROM users WHERE email = ?"
    elif type == 'id':
        chsch = "SELECT 1 FROM users WHERE id = ?"
    elif type == 'postid':
        chsch = "SELECT 1 FROM posts WHERE id = ?"
    elif type == 'comid':
        chsch = "SELECT 1 FROM commentss WHERE id = ?"
    cursor.execute(chsch, (input,))
    return cursor.fetchone()

def isCorrect(userid,pswd):
    db = get_db()
    cursor = db.cursor()
    chsch = "SELECT pswd FROM users WHERE id = ?"
    cursor.execute(chsch, (userid,))
    result = cursor.fetchone()
    return result[0] == pswd

#create
def create_user(user,email,pswd):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO users (username, email, pswd, avatar) VALUES (?,?,?,?)"
    cursor.execute(insch, (user,email,pswd,"/static/uploads/defavt.png"))
    db.commit()

def create_post(mmnt,capt,userid):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO posts (userid, caption, postimg) VALUES (?,?,?)"
    cursor.execute(insch, (userid,capt,mmnt))
    db.commit()

#comment lookup
def get_post_comment_info(postid):
    comments = []
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT * FROM commentss WHERE postid = ? ORDER BY created_at DESC"
    cursor.execute(sch,(postid,))
    dbcommentinfo = cursor.fetchall()
    for c in dbcommentinfo:
        userinfo = get_short_user_info(c[1])
        comment = [c,userinfo]
        comments.append(comment)
    return comments

def get_post_comment_count(postid):
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT COUNT(*) FROM commentss WHERE postid = ?"
    cursor.execute(sch,(postid,))
    count = cursor.fetchone()[0]
    return count

#post lookup
def get_posts(userid, curuser):
    posts = []
    db = get_db()
    cursor = db.cursor()
    if userid == '*':
        cursor.execute("SELECT * FROM posts ORDER BY created_at DESC, id DESC")
    else: 
        sch = "SELECT * FROM posts WHERE userid = ? ORDER BY created_at DESC, id DESC"
        cursor.execute(sch, (userid,))
    dbpostsinfo = cursor.fetchall()
    for p in dbpostsinfo:
        userinfo = get_short_user_info(p[1])
        likeinfo = []
        likeinfo.append(get_like_count(p[0]))
        likeinfo.append(is_liked(p[0],curuser))
        post = [p,userinfo,likeinfo]
        posts.append(post)
    for p in posts:
        commentinfo = get_post_comment_info(p[0][0])
        p.append([commentinfo,get_post_comment_count(p[0][0])])
    return posts

#update
def update_info(userid, new, parameter):
    db = get_db()
    cursor = db.cursor()
    if parameter == 'avatar':
        upsch = "UPDATE users SET avatar = ? WHERE id = ?"
    elif parameter == 'password':
        upsch = "UPDATE users SET pswd = ? WHERE id = ?"
    elif parameter == 'username':
        upsch = "UPDATE users SET username = ? WHERE id = ?"
    elif parameter == 'email':
        upsch = "UPDATE users SET email = ? WHERE id = ?"
    elif parameter == 'admin':
        upsch = "UPDATE users SET isadmin = ? WHERE id = ?"
    cursor.execute(upsch, (new, userid))
    db.commit()

def toggle_admin(userid):
    if get_db_user_info(userid)[6]:
        update_info(userid, 0, "admin")
    else:
        update_info(userid, 1, "admin")

#delete
def delete_user(userid):
    db = get_db()
    cursor = db.cursor()
    delsch = "DELETE FROM users WHERE id = ?"
    cursor.execute(delsch, (userid,))
    db.commit()

def delete_post(postid):
    db = get_db()
    cursor = db.cursor()
    delsch = "DELETE FROM posts WHERE id = ?"
    cursor.execute(delsch, (postid,))
    db.commit()

#Likes
def toggle_like(postid,userid):
    db = get_db()
    cursor = db.cursor()
    liksch = "SELECT 1 FROM likes WHERE userid = ? AND postid = ?"
    cursor.execute(liksch, (userid,postid))
    if cursor.fetchone():
        liksch = "DELETE FROM likes WHERE userid = ? AND postid = ?"  
    else:
        liksch = "INSERT INTO likes (userid,postid) VALUES (?,?)"
    cursor.execute(liksch,(userid,postid))
    db.commit()

def get_like_count(postid):
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT COUNT(*) FROM likes WHERE postid = ?"
    cursor.execute(sch,(postid,))
    count = cursor.fetchone()[0]
    return count

def is_liked(postid,curuserid):
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT 1 FROM likes WHERE postid = ? AND userid = ?"
    cursor.execute(sch,(postid,curuserid))
    if cursor.fetchone():
        return True
    return False

#follows
def toggle_follow(eeid,erid):
    db = get_db()
    cursor = db.cursor()
    flwsch = "SELECT 1 FROM follow WHERE fee = ? AND fer = ?"
    cursor.execute(flwsch, (eeid,erid))
    if cursor.fetchone():
        flwsch = "DELETE FROM follow WHERE fee = ? AND fer = ?"  
    else:
        flwsch = "INSERT INTO follow (fee,fer) VALUES (?,?)"
    cursor.execute(flwsch,(eeid,erid))
    db.commit()

def get_follow_count(eeid):
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT COUNT(*) FROM follow WHERE fee = ?"
    cursor.execute(sch,(eeid,))
    count = cursor.fetchone()[0]
    return count

def is_followed(eeid, erid):
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT 1 FROM follow WHERE fee = ? AND fer = ?"
    cursor.execute(sch,(eeid,erid))
    if cursor.fetchone():
        return True
    return False

#userlookup
def get_short_user_info(userid):
    shortinfo = []
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT username,avatar FROM users WHERE id = ?"
    cursor.execute(sch,(userid,))
    result = cursor.fetchone()
    for i in range(2):
        shortinfo.append(result[i])
    shortinfo.append(get_tag_info(userid))
    shortinfo.append(userid)
    return shortinfo

def get_db_user_info(userid):
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT * FROM users WHERE id = ?"
    cursor.execute(sch, (userid,))
    result = cursor.fetchone()
    userinfo = []
    for i in range(8):
        userinfo.append(result[i])
    return userinfo

def get_tag_info(userid):
    db = get_db()
    cursor = db.cursor()
    taginfo = []
    isadmin = get_db_user_info(userid)[6]
    if userid == 0:
        taginfo.append('Owner')
        taginfo.append("#ff0000")
        taginfo.append(0)
    elif isadmin == True:
        taginfo.append('Admin')
        taginfo.append("#00ff00")
        taginfo.append(1)
    else:
        taginfo.append('User')
        taginfo.append("#0000ff")
        taginfo.append(2)
    return taginfo

def get_all_user_info(userid,curuserid):
    allinfo = []
    dbuserinfo = get_db_user_info(userid)
    followerinfo = []
    followerinfo.append(get_follow_count(userid))
    followerinfo.append(is_followed(userid,curuserid))
    taginfo = get_tag_info(userid)
    allinfo.append(dbuserinfo)
    allinfo.append(followerinfo)
    allinfo.append(taginfo)
    return allinfo

def get_users():
    users = []
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT id FROM users ORDER BY id"
    cursor.execute(sch)
    result = cursor.fetchall()
    for id in result:
        user = get_short_user_info(id[0])
        users.append(user)
    return users

def identify(username):
    db = get_db()
    cursor = db.cursor()
    idsch = "SELECT id FROM users WHERE username = ?"
    cursor.execute(idsch,(username,))
    result = cursor.fetchone()
    return result[0]  

def postid_to_userid(postid):
    db = get_db()
    cursor = db.cursor()
    idsch = "SELECT userid FROM posts WHERE id = ?"
    cursor.execute(idsch,(postid,))
    result = cursor.fetchone()
    return result[0]

#comments
def comment_on_post(postid, userid, c):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO commentss (postid, userid, contents) VALUES (?,?,?)"
    cursor.execute(insch, (postid,userid,c))
    db.commit()

def comid_to_userid(comid):
    db = get_db()
    cursor = db.cursor()
    idsch = "SELECT userid FROM commentss WHERE id = ?"
    cursor.execute(idsch,(comid,))
    result = cursor.fetchone()
    return result[0]

def comid_to_postid(comid):
    db = get_db()
    cursor = db.cursor()
    idsch = "SELECT postid FROM commentss WHERE id = ?"
    cursor.execute(idsch,(comid,))
    result = cursor.fetchone()
    return result[0]

def delete_comment(comid):
    db = get_db()
    cursor = db.cursor()
    delsch = "DELETE FROM commentss WHERE id = ?"
    cursor.execute(delsch, (comid,))
    db.commit()

#reports
def get_reports():
    reports = []
    db = get_db()
    cursor = db.cursor()
    sch = "SELECT * FROM reports"
    cursor.execute(sch)
    result = cursor.fetchall()
    for r in result:
        report = []
        reportinfo = []
        for i in range(5):
            reportinfo.append(r[i])
        report.append(reportinfo)
        shortinfo = get_short_user_info(reportinfo[1])
        report.append(shortinfo)
        reports.append(report)
    return reports

        


def create_report(reason,details,userid):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO reports (userid, reason, details) VALUES (?,?,?)"
    cursor.execute(insch, (userid,reason,details))
    db.commit()