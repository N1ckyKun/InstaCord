import sqlite3, base64, mimetypes
from flask import g, url_for 

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("insta.db")
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    schema = open("schema.sql")
    db.executescript(schema.read())

def exists(input, type):
    db = get_db()
    cursor = db.cursor()
    if type == 'user':
        chsch = "SELECT 1 FROM users WHERE username = ?"
        cursor.execute(chsch, (input,))
        return cursor.fetchone()
    elif type == 'email':
        chsch = "SELECT 1 FROM users WHERE email = ?"
        cursor.execute(chsch, (input,))
        return cursor.fetchone()

def isCorrect(userid,pswd):
    db = get_db()
    cursor = db.cursor()
    chsch = "SELECT pswd FROM users WHERE id = ?"
    cursor.execute(chsch, (userid,))
    result = cursor.fetchone()
    return result[0] == pswd

def create_user(user,email,pswd):
    db = get_db()
    cursor = db.cursor()
    with open('static/defavt.png', 'rb') as file:
            encd_bytes = base64.b64encode(file.read()).decode('utf-8')
            data_uri = f"data:image/png;base64,{encd_bytes}" 
    insch = "INSERT INTO users (username, email, pswd, avatar) VALUES (?,?,?,?)"
    cursor.execute(insch, (user,email,pswd,data_uri))
    db.commit()

def create_post(mmnt,capt,userid):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO posts (userid, caption, postimg) VALUES (?,?,?)"
    cursor.execute(insch, (userid,capt,mmnt))
    db.commit()

def get_posts(userid, curuser):
    db = get_db()
    cursor = db.cursor()
    if userid == '*':
        cursor.execute("SELECT * FROM posts ORDER BY created_at DESC, id DESC")
    else: 
        pstsch = "SELECT * FROM posts WHERE userid = ? ORDER BY created_at DESC, id DESC"
        cursor.execute(pstsch, (userid,))
    result = cursor.fetchall()
    posts = []
    for p in result:
        avtsch = "SELECT avatar,username FROM users WHERE id = ?"
        cursor.execute(avtsch,(p[1],))
        result = cursor.fetchone()
        avtr = result[0]
        user = result[1]
        likes = check_likes(p[0],curuser)
        post = [p[0],user,avtr,p[2],p[3],p[4],likes[0],likes[1]]
        posts.append(post)
    return posts

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
    cursor.execute(upsch, (new, userid))
    db.commit()

def get_user_info(userid,curuserid):
    db = get_db()
    cursor = db.cursor()
    usrsch = "SELECT * FROM users WHERE id = ?"
    cursor.execute(usrsch, (userid,))
    result = cursor.fetchone()
    info = []
    for i in range(0,5):
        info.append(result[i])
    follows = check_follows(info[0],curuserid)
    info.append(follows[0])
    info.append(follows[1])
    return info

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

def check_likes(postid, userid):
    db = get_db()
    cursor = db.cursor()
    liksch = "SELECT COUNT(*) FROM likes WHERE postid = ?"
    cursor.execute(liksch,(postid,))
    count = cursor.fetchone()[0]
    liksch = "SELECT 1 FROM likes WHERE postid = ? AND userid = ?"
    cursor.execute(liksch,(postid,userid))
    if cursor.fetchone():
        return count, 1
    return count, 0

def check_follows(eeid, erid):
    db = get_db()
    cursor = db.cursor()
    flwsch = "SELECT COUNT(*) FROM follow WHERE fee = ?"
    cursor.execute(flwsch,(eeid,))
    count = cursor.fetchone()[0]
    print(count)
    flwsch = "SELECT 1 FROM follow WHERE fee = ? AND fer = ?"
    cursor.execute(flwsch,(eeid,erid))
    if cursor.fetchone():
        return count, True
    return count, False

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