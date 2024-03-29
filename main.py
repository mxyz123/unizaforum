import datetime
import re
import flask
import uuid
from flask import Flask, render_template, request, redirect, jsonify
import logging
import os
from logging.handlers import RotatingFileHandler
from time import strftime
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Integer, DateTime, select, table, column, desc, asc
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
    media: Mapped[str] = mapped_column(String, nullable=True)
    thread_id: Mapped[int] = mapped_column(Integer, nullable=False)
    creator: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Thread(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subforum_id: Mapped[int] = mapped_column(Integer, nullable=False)
    main_post_id: Mapped[int] = mapped_column(Integer, nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubForum(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    short: Mapped[str] = mapped_column(String, nullable=False, unique=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/_get_threads/<string:sub_name>")
def get_threads(sub_name):
    threads = []
    try:
        sub_forum = SubForum.query.filter_by(name=sub_name.lower()).first()
        response = Thread.query.order_by(desc(Thread.date)).filter_by(subforum_id=sub_forum.id).all()
    except:
        return jsonify(threads)
    for r in response:
        if r.main_post_id is not None:
            main_post = Post.query.filter_by(id=r.main_post_id).first()
            threads.append({'id': str(r.id), 'subforum_id': str(r.subforum_id), 'message': str(main_post.message),
                            'media': str(main_post.media), 'date': str(r.date), 'creator': str(main_post.creator)
                            })
    return jsonify(threads)


@app.route("/<string:sub_name>")
def subforum(sub_name):
    check = SubForum.query.filter_by(name=sub_name).first()
    if check is None:
        flask.abort(404)
    return render_template('subforum.html', subName=sub_name.upper())


@app.route("/_get_posts/<string:sub_name>/<string:thread_id>")
def get_posts(sub_name, thread_id):
    response = []
    posts = Post.query.order_by(asc(Post.date)).filter_by(thread_id=thread_id).all()
    for p in posts:
        response.append({
            'id': str(p.id), 'thread_id': str(p.thread_id), 'message': str(p.message), 'media': str(p.media),
            'date': str(p.date), 'creator': str(p.creator)
        })
    return jsonify(response)


@app.route("/<string:sub_name>/<string:thread_id>/create_post", methods=["GET", "POST"])
@login_required
def post(sub_name, thread_id):
    check1 = SubForum.query.filter_by(name=sub_name).first()
    check2 = Thread.query.filter_by(id=thread_id).first()
    if check1 is None or check2 is None:
        flask.abort(404)
    if request.method == 'POST':
        if request.form["message"] == '' and len(request.files) <= 0:
            return render_template('thread.html', sub_name=sub_name.upper(), thread_id=thread_id, hasErr=True,
                                   errCode=13)
        create_post(request.form['message'], thread_id, request.files['file'])
    return redirect(f'/{sub_name.lower()}/{thread_id}')


@app.route("/edit_post/<string:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    p = Post.query.filter_by(id=post_id).first()
    if current_user.username != p.creator:
        flask.abort(404)
    if request.method == "POST":
        if request.form["edit_msg"] != "":
            p.message = request.form["edit_msg"]
        if request.files["edit_file"].filename != "":
            f = request.files["edit_file"]
            if p.media is not None:
                os.remove(f'static/media/{p.media}')
            unique_filename = str(uuid.uuid4().hex)
            media = None
            if f.filename.endswith('.png') or f.filename.endswith('.jpg') or f.filename.endswith('.jpeg'):
                f.save(f"static/media/{unique_filename}.png")
                media = f"{unique_filename}.png"
            elif f.filename.endswith('.gif'):
                f.save(f"static/media/{unique_filename}.gif")
                media = f"{unique_filename}.gif"
            p.media = media
        db.session.commit()
    t = Thread.query.filter_by(id=p.thread_id).first()
    sub = SubForum.query.filter_by(id=t.subforum_id).first()
    return redirect(f'/{sub.name}/{t.id}')


@app.route("/_delete_post/<string:sub_name>/<string:thread_id>/<string:post_id>", methods=["GET", "POST"])
@login_required
def delete_post(sub_name, thread_id, post_id):
    p = Post.query.filter_by(id=int(post_id)).first()
    print(p.id)
    if current_user.username == p.creator or current_user.admin:
        try:
            t = Thread.query.filter_by(main_post_id=p.id).first()
            if t is not None:
                posts = Post.query.filter_by(thread_id=t.id).all()
                for po in posts:
                    if po.id != p.id:
                        if po.media != "None":
                            os.remove(f"static/media/{po.media}")
                        db.session.delete(po)
                db.session.delete(t)
        except:
            pass
        os.remove(f"static/media/{p.media}")
        db.session.delete(p)
        db.session.commit()
    return redirect(f'/{sub_name.lower()}/{thread_id}')


@app.route("/<string:sub_name>/<string:thread_id>")
def thread(sub_name, thread_id):
    try:
        t = Thread.query.filter_by(id=thread_id).first()
        if t is None:
            flask.abort(404)
    except:
        flask.abort(404)
    return render_template('thread.html', sub_name=sub_name.upper(), thread_id=thread_id)


@app.route("/admin/create_sub", methods=["GET", "POST"])
@login_required
def admin_sub():
    if not current_user.admin:
        flask.abort(404)
    if request.method == "POST":
        if request.form["name"] == '':
            return render_template('admin_thread.html', hasErr=True, errCode=12)
        if request.form["short"] == '':
            return render_template('admin_thread.html', hasErr=True, errCode=14)
        check = SubForum.query.filter_by(name=request.form["name"]).first()
        if check is not None:
            return render_template('admin_thread.html', hasErr=True, errCode=15)
        check = SubForum.query.filter_by(short=request.form["short"]).first()
        if check is not None:
            return render_template('admin_thread.html', hasErr=True, errCode=16)
        sub = SubForum(name=request.form["name"], short=request.form["short"])
        db.session.add(sub)
        db.session.commit()
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        print(f'{timestamp} Sub forum {sub.name} created.')
    return render_template('admin_thread.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["email"] == '':
            return render_template('login.html', hasErr=True, errCode=1)
        if request.form["password"] == '':
            return render_template('login.html', hasErr=True, errCode=2)
        if current_user.is_authenticated:
            return render_template('login.html', hasErr=True, errCode=9)
        user = User.query.filter_by(email=request.form["email"]).first()
        if user:
            if hashing.compare(request.form["password"], user.pswd):
                login_user(user)
                return render_template("login.html", hasErr=True, errCode=7)
        else:
            return render_template('login.html', hasErr=True, errCode=6)
    return render_template('login.html')


def create_post(message, thread_id, f):
    unique_filename = str(uuid.uuid4().hex)
    media = None
    if not f.filename == "":
        if f.filename.endswith('.png') or f.filename.endswith('.jpg') or f.filename.endswith('.jpeg'):
            f.save(f"static/media/{unique_filename}.png")
            media = f"{unique_filename}.png"
        elif f.filename.endswith('.gif'):
            f.save(f"static/media/{unique_filename}.gif")
            media = f"{unique_filename}.gif"
    new_post = Post(message=message, thread_id=thread_id, media=media, creator=current_user.username)
    db.session.add(new_post)
    db.session.commit()
    return new_post.id


@app.route("/<string:sub_name>/create_thread", methods=["GET", "POST"])
@login_required
def create_thread(sub_name):
    check = SubForum.query.filter_by(name=sub_name).first()
    if check is None:
        flask.abort(404)
    if request.method == "POST":
        if request.form["message"] == '' and len(request.files) <= 0:
            return render_template('subforum.html', subName=sub_name.upper(), hasErr=True, errCode=13)
        _sub_forum = SubForum.query.filter_by(name=sub_name).first()
        new_thread = Thread(subforum_id=_sub_forum.id)
        db.session.add(new_thread)
        db.session.commit()
        new_thread.main_post_id = create_post(request.form["message"], new_thread.id, request.files['file'])
        db.session.commit()
    return redirect(f"/{sub_name}")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form["meno"] == '':
            return render_template('register.html', hasErr=True, errCode=0)
        if request.form["email"] == '':
            return render_template('register.html', hasErr=True, errCode=1)
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if not re.fullmatch(regex, request.form["email"]):
            return render_template('register.html', hasErr=True, errCode=11)
        if request.form["password"] == '' or request.form["password2"] == '':
            return render_template('register.html', hasErr=True, errCode=2)
        if request.form["password"] != request.form["password2"]:
            return render_template('register.html', hasErr=True, errCode=3)
        check = User.query.filter_by(username=request.form["meno"]).first()
        if check is not None:
            return render_template('register.html', hasErr=True, errCode=4)
        check = User.query.filter_by(email=request.form["email"]).first()
        if check is not None:
            return render_template('register.html', hasErr=True, errCode=5)
        user = User(
            username=request.form["meno"],
            email=request.form["email"],
            pswd=encrypt(request.form["password"])
        )
        db.session.add(user)
        db.session.commit()
        copy("static/pfp/pfp_.png", f"static/pfp/{user.username}.png")
        return render_template("login.html", hasErr=True, errCode=8)
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


@app.route("/admin/delete_thread", methods=["GET", "POST"])
@login_required
def admin_delete_thread():
    if current_user.admin is True and request.method == "POST":
        if request.form["name"] == "":
            return render_template("delete_thread.html", hasErr=True, errCode=10)
        t = Thread.query.filter_by(id=int(request.form["name"])).first()
        posts = Post.query.filter_by(thread_id=t.id).all()
        for p in posts:
            os.remove(f"static/media/{p.media}")
            db.session.delete(p)
        db.session.delete(t)
        db.session.commit()
    return render_template("delete_thread.html")


@app.route("/admin/delete_sub", methods=["GET", "POST"])
@login_required
def admin_delete_sub():
    if current_user.admin is True and request.method == "POST":
        if request.form["name"] == "":
            return render_template("deletesub.html", hasErr=True, errCode=10)
        s = SubForum.query.filter_by(name=request.form["name"]).first()
        threads = Thread.query.filter_by(subforum_id=s.id).all()
        for t in threads:
            posts = Post.query.filter_by(thread_id=t.id).all()
            for p in posts:
                os.remove(f"static/media/{p.media}")
                db.session.delete(p)
            db.session.delete(t)
        db.session.delete(s)
        db.session.commit()
    return render_template("deletesub.html")


@app.route("/profile")
@login_required
def user_profile():
    return render_template('profile.html', username=current_user.username, isAdmin=current_user.admin,
                           hasGif=current_user.gif, crDate=current_user.date, bio=current_user.bio)


@app.route("/fora")
def forums():
    subs = SubForum.query.all()
    return render_template('forum.html', forums=subs)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        if request.form["password"] == request.form["password2"] and request.form["password"] != "":
            if hashing.compare(request.form["password"], current_user.pswd):
                if current_user.gif is True:
                    os.remove(f"static/pfp/{current_user.username}.gif")
                else:
                    os.remove(f"static/pfp/{current_user.username}.png")
                db.session.delete(current_user)
                db.session.commit()
                logout_user()
                return redirect("/")
            else:
                return render_template('edit_profile.html', hasErr=True, errCode=6)
        user = User.query.filter_by(username=current_user.username).first()
        if not (request.form["pswd"] == '' or request.form["newPswd"] == ''):
            if hashing.compare(request.form["pswd"], user.pswd):
                user.pswd = encrypt(request.form["newPswd"])
                db.session.commit()
            else:
                return render_template('edit_profile.html', hasErr=True, errCode=6)
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
                else:
                    return render_template('edit_profile.html', hasErr=True, errCode=10)
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
