import datetime

import flask
from flask import Flask, render_template, request, redirect
import logging
import os
from logging.handlers import RotatingFileHandler
from time import strftime
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

import hashing
from hashing import encrypt
from shutil import copy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
database = "uniza_forum.db"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + database
app.config["SECRET_KEY"] = "test_secret"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    pswd: Mapped[str] = mapped_column(String, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bio: Mapped[str] = mapped_column(String, nullable=True)
    gif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Post(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(String, nullable=True)
    image: Mapped[str] = mapped_column(String, nullable=True)
    thread_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Thread(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/fri")
def fri():
    return render_template('fri.html')


@app.route("/fri/inf")
def inf():
    return render_template('INF.html')


@app.route("/fri/mat")
def mat():
    return render_template('MAT.html')


@app.route("/fri/anj")
def anj():
    return render_template('ANJ.html')


@app.route("/feit")
def feit():
    return render_template('feit.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not (request.form["email"] == '' or request.form["password"] == ''):
            user = User.query.filter_by(email=request.form["email"]).first()
            if user:
                if hashing.compare(request.form["password"], user.pswd):
                    login_user(user)
    return render_template('login.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not (request.form["meno"] == '' or request.form["email"] == '' or request.form["password"] == '' or
                request.form["password2"] == '' or request.form["password"] != request.form["password2"]):
            # noinspection PyArgumentList
            user = User(
                username=request.form["meno"],
                email=request.form["email"],
                pswd=encrypt(request.form["password"])
            )
            db.session.add(user)
            db.session.commit()
            copy("static/pfp/pfp_.png", f"static/pfp/{user.username}.png")
            return redirect("/login")
    return render_template('register.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/profile/<string:username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', username=user.username, isAdmin=user.admin, hasGif=user.gif,
                           crDate=user.date, bio=user.bio)


@app.route("/profile")
@login_required
def user_profile():
    return render_template('profile.html', username=current_user.username, isAdmin=current_user.admin,
                           hasGif=current_user.gif, crDate=current_user.date, bio=current_user.bio)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        user = User.query.filter_by(username=current_user.username).first()
        if not (request.form["pswd"] == '' or request.form["new_pswd"] == ''):
            if hashing.compare(request.form["pswd"], user.pswd):
                user.pswd = encrypt(request.form["new_pswd"])
                db.session.commit()
        if not request.form['bio'] == '':
            user.bio = request.form['bio']
            db.session.commit()
        if 'file' in request.files:
            f = request.files['file']
            if not f.filename == "":
                if f.filename.endswith('.png') or f.filename.endswith('.jpg') or f.filename.endswith('.jpeg'):
                    f.save(f"static/pfp/{current_user.username}.png")
                    try:
                        os.remove(f"static/pfp/{current_user.username}.gif")
                    except:
                        pass
                    user.gif = False
                    db.session.commit()
                elif f.filename.endswith('.gif'):
                    f.save(f"static/pfp/{current_user.username}.gif")
                    try:
                        os.remove(f"static/pfp/{current_user.username}.png")
                    except:
                        pass
                    user.gif = True
                    db.session.commit()
        return redirect("/profile/edit")
    return render_template('edit_profile.html')


@app.route("/admin")
@login_required
def admin():
    if not current_user.admin:
        flask.abort(404)
    users = User.query.all()
    return render_template("admin_dashboard.html", users=users)


@app.route("/admin/delete/<string:username>")
@login_required
def delete(username):
    if not current_user.admin:
        flask.abort(404)
    user = User.query.filter_by(username=username).first()
    db.session.delete(user)
    db.session.commit()
    if not user.gif:
        os.remove(f"static/pfp/{username}.png")
    else:
        os.remove(f"static/pfp/{username}.gif")
    return redirect("/admin")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    logger.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path,
                 response.status)
    return response


if __name__ == '__main__':
    PORT = 8080
    if not os.path.exists("instance/" + database):
        with app.app_context():
            db.create_all()
    from waitress import serve
    from paste.translogger import TransLogger

    handler = RotatingFileHandler('uniza_forum.log', maxBytes=100000, backupCount=3)
    logger = logging.getLogger('tdm')
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    print(f"Local website running on: http://127.0.0.1:{PORT}")
    serve(TransLogger(app), host="0.0.0.0", port=PORT)
