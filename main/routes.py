from flask import render_template, url_for, redirect, flash,request
from main import app,db,bcrypt
from main.models import User, Post
from main.forms import SignUpForm, LoginForm
from flask_login import login_user,current_user,logout_user,login_required

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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page=request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash(f'Loign Unsuccessful! Please check email and password', 'danger')
    return render_template('login.html', form=form, title="Login")

@app.route('/account')
@login_required
def account():
    return render_template('account.html',title='Account')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
