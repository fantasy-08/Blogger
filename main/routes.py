import os
import secrets
from PIL import Image
from flask import render_template, url_for, redirect, flash,request, abort
from main import app,db,bcrypt,mail
from main.models import User, Post
from main.forms import SignUpForm, LoginForm,UpdateAccountForm ,PostForm,RequestResetForm,ResetPasswoardForm
from flask_login import login_user,current_user,logout_user,login_required
from flask_mail import Message

@app.route('/')
@app.route("/home")
def home():
    page=request.args.get('page',1,type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=3)
    return render_template('home.html', posts=posts)

@app.route("/user/<string:username>")
def user_post(username):
    page=request.args.get('page',1,type=int)
    user=User.query.filter_by(username=username)\
        .first_or_404()
    posts=Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
            .paginate(page=page,per_page=3)
    return render_template('user_post.html',user=user,posts=posts)

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

def save_picture(form_picture):
    hex=secrets.token_hex(8)
    _,extension=os.path.splitext(form_picture.filename)
    picture=hex+extension
    pic_path=os.path.join(app.root_path,'static/picture',picture)

    output_size=(125,125)
    image_new=Image.open(form_picture)
    image_new.thumbnail(output_size)

    image_new.save(pic_path)

    return picture

@app.route('/account',methods=['GET','POST'])
@login_required
def account():
    form= UpdateAccountForm()
    if form.validate_on_submit():

        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            current_user.image_file=picture_file

        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('Account update','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    image_file=url_for('static',filename='picture/'+current_user.image_file)
    return render_template('account.html',title='Account',image_file=image_file,form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/post/new',methods=['GET','POST'])
@login_required
def new_post():
    form =PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data,content=form.content.data,author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Blog added to community','success')
        return redirect(url_for('home'))
    return render_template('new_post.html',form=form,titlt="NEW BLOG")

@app.route('/post/<int:post_id>')
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html',title=post.title,post=post)

@app.route('/post/<int:post_id>/update',methods=['GET','POST'])
@login_required
def update(post_id):
    
    post=Post.query.get_or_404(post_id)

    if post.author!=current_user:
        abort(403)
    form=PostForm()
        
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Blog updated successfully','success')
        return redirect(url_for('post',post_id=post_id))
    elif request.method=='GET':
        form.title.data=post.title
        form.content.data=post.content

    return render_template('update_post.html',form=form,post=post)

@app.route('/post/<int:post_id>/delete',methods=['POST'])
@login_required
def delete_post(post_id):
    
    post=Post.query.get_or_404(post_id)

    if post.author!=current_user:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    flash('Blog deleted','danger')
    return redirect(url_for('home'))

def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message('Password Reset Request',sender='codechefmnit@gmail.com',recipients=[user.email])
    msg.body=f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/reset_password',methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form =RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with password','info')
        return redirect(url_for('login'))
    return render_template('reset_request.html',titlt="Reset Password",form=form)

@app.route('/reset_password/<token>',methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user=User.verify_reset_token(token)
    if not user:
        flash('Opps invalid or expired token (30min only)','warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswoardForm()
    if form.validate_on_submit():
        hashPassword=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashPassword
        db.session.commit()
        flash(f'Password Changed Now you can login', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',titlt="Change Password",form=form)

