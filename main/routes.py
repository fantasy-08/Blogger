from flask import render_template, url_for, redirect, flash
from main import app,db,bcrypt
from main.models import User, Post
from main.forms import SignUpForm, LoginForm

posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]
@app.route('/')
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hashPassword=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data,email=form.email.data,password=hashPassword)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! Now you can login', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form, title="SignUp")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Loign successful {form.email.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('login.html', form=form, title="Login")
