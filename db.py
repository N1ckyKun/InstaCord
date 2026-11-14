import sqlite3, base64, mimetypes
from flask import g, url_for 

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("insta.db")
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    schema = open("schema.sql")
    db.executescript(schema.read())

def insert_user(user,email,pswd):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO users (username, email, pswd, avatar) VALUES (?,?,?,?)"
    cursor.execute(insch, (user,email,pswd,'123'))
    db.commit()

def it_exists(input, type):
    db = get_db()
    cursor = db.cursor()
    if type == 'usr':
        chsch = "SELECT username FROM users WHERE username = ?"
        cursor.execute(chsch, (input,))
        result = cursor.fetchone()
        if result:
            return True
        return False
    elif type == 'eml':
        chsch = "SELECT email FROM users WHERE email = ?"
        cursor.execute(chsch, (input,))
        result = cursor.fetchone()
        if result:
            return True
        return False


def compare_pswd(user,pswd):
    db = get_db()
    cursor = db.cursor()
    chsch = "SELECT pswd FROM users WHERE username = ?"
    cursor.execute(chsch, (user,))
    result = cursor.fetchone()
    return result[0] == pswd

def create_post(mmnt,capt,dscrpt,user):
    db = get_db()
    cursor = db.cursor()
    insch = "INSERT INTO posts (userid, caption, dscrpt, postimg) VALUES (?,?,?,?)"
    cursor.execute(insch, (user,capt,dscrpt,mmnt))
    db.commit()

def get_posts():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts")
    result = cursor.fetchall()
    posts = []
    with open('static/defavt.png', 'rb') as file:
        encd_bytes = base64.b64encode(file.read()).decode('utf-8')
        data_uri = f"data:image/png;base64,{encd_bytes}" 
    for p in result:
        avtsch = "SELECT avatar FROM users WHERE username = ?"
        cursor.execute(avtsch,(p[1],))
        avtr = cursor.fetchone()[0]
        if avtr == '123':
            avtr = data_uri
            print(data_uri)
        post = [p[1],p[2],p[3],p[4],p[5],avtr]
        posts.append(post)
    return posts
