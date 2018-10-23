from flask import Flask, redirect, request, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
import hashlib, random, string
import cgi
import os

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(2000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref="owner")

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.route('/')
def index():
    users = User.query.all()        
    return render_template('users.html', users=users)


@app.route('/blog') # why is blog undefined?
def blog():
    blogs = Blog.query.all()
    id = request.args.get('id')
    if id:
        blog = Blog.query.filter_by(id=id).first()
        return render_template('users_blog.html', blog=blog)
    user = request.args.get('user')
    if user:
        user_blogs = Blog.query.filter_by(owner_id=user).all()
        return render_template('blogs.html', blogs=user_blogs)
    return render_template('blogs.html', blogs=blogs)

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    if request.method == 'POST':
        blog_title = request.form['blog_title']
        blog_content = request.form['blog_content']
        owner = User.query.filter_by(username = session['username']).first()
      
        if blog_title.strip() == '':
            flash("You forgot to add a blog title", "error")
            return redirect("/newpost")
        if blog_content.strip() == '':
            flash("You forgot to write your post", "error")
            return redirect("/newpost")
        #for some reason i cant get the categories working, does it have to do with redirecting?
        blog = Blog(blog_title, blog_content, owner)
        db.session.add(blog)
        db.session.commit()
        return redirect("./blog?id={0}".format(blog.id)) #why is blog lowercase?
    return render_template('add_a_new_post.html')

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

def make_salt():
    return ''.join([random.choice(string.ascii_letters) for x in range(5)])

def make_pw_hash(password, salt=None):
    if not salt:
        salt = make_salt()
    salt = make_salt()
    hash = hashlib.sha256(str.encode(password + salt)).hexdigest()
    return '{0},{1}'.format(hash, salt)

def check_pw_hash(password, hash):
    salt = hash.split(',')[1]#this takes only the salt from the hash
    if make_pw_hash(password, salt) == hash:
        return True
    return False

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            flash("Logged in")
            return redirect('/')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        username_error= ''
        password_error = ''
        verify_error = ''
        email_error = ''

        if username == '':
            flash("That is not a valid username", category='error')
        elif ' ' in username:
            flash('that is not a valid username', category='error')
        
        if password == '':
            flash('That is not a valid password', category='error')
        elif ' ' in password:
            flash('That is not a valid password', category='error')
        elif len(password) <= 3 or len(password) > 30:
            flash('that is not a valid password', category='error')
        
        if verify != password:
            flash('those passwords do not match', category='error')
        elif len(username) > 20:

            flash('your username is too long', category='error')

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/')
        else:
            flash("Duplicate User")
            return redirect('/signup')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

    

if __name__ == '__main__':
    app.run()