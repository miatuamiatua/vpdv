from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
	jsonify, current_app, send_file
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm
from app.models import User, Post
from app.translate import translate
from app.main import bp
import json
from werkzeug.utils import secure_filename
import os
from app.main.forms import MessageForm
from app.models import Message
from app.models import Notification

ALLOWED_EXTENSIONS = set(["png"])

def allowed_file(filename):
	return "." in filename and \
		   filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


@bp.before_app_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()
		g.search_form = SearchForm()
	g.locale = str(get_locale())


@bp.route("/", methods=["GET", "POST"])
def root():
	if current_user.is_authenticated:
		return redirect(url_for("main.index"))
	return render_template("intro.html")
@bp.route("/feed", methods=["GET", "POST"])
@login_required
def index():
	form = PostForm()
	if form.validate_on_submit():
		language = guess_language(form.post.data)
		if language == "UNKNOWN" or len(language) > 5:
			language = ""
		post = Post(body=form.post.data, author=current_user,
					language=language)
		db.session.add(post)
		db.session.commit()
		flash(_("Пост опубликован!"))
		return redirect(url_for("main.index"))
	#flash(_(""))
	page = request.args.get("page", 1, type=int)
	posts = current_user.followed_posts().paginate(
		page, current_app.config["POSTS_PER_PAGE"], False)
	next_url = url_for("main.index", page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for("main.index", page=posts.prev_num) \
		if posts.has_prev else None
	return render_template("index.html", title=_("Лента"), form=form,
						   posts=posts.items, next_url=next_url,
						   prev_url=prev_url, time=str(datetime.utcnow())[0:-10], path=request.full_path, i=0)

@bp.route("/all")
@login_required
def explore():
	page = request.args.get("page", 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config["POSTS_PER_PAGE"], False)
	next_url = url_for("main.explore", page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for("main.explore", page=posts.prev_num) \
		if posts.has_prev else None
	return render_template("index.html", title=_("Все посты"),
						   posts=posts.items, next_url=next_url,
						   prev_url=prev_url, time=str(datetime.utcnow())[0:-10], path=request.base_url)


@bp.route("/user/<username>")
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get("page", 1, type=int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config["POSTS_PER_PAGE"], False)
	next_url = url_for("main.user", username=user.username,
					   page=posts.next_num) if posts.has_next else None
	prev_url = url_for("main.user", username=user.username,
					   page=posts.prev_num) if posts.has_prev else None
	form = EmptyForm()
	return render_template("user.html", user=user, title=_("@" + user.username),posts=posts.items,
						   next_url=next_url, prev_url=prev_url, form=form, time=str(datetime.utcnow())[0:-10], 
						   last_seen=str(user.last_seen)[0:-10], path=request.full_path)


@bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
	form = EditProfileForm(current_user.username)
	if form.validate_on_submit():
		os.rename("/media/boris/Файлы/Код/fatolj/latest/app/avatars/" + current_user.username +".png", "/media/boris/Файлы/Код/fatolj/latest/app/avatars/" + form.username.data +".png")
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		db.session.commit()
		flash(_("Сохранено!"))
		return redirect(url_for("main.user", username=current_user.username))
	elif request.method == "GET":
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
	return render_template("edit_profile.html", title=_("Редактирование профиля"),
						   form=form)


@bp.route("/follow/<username>", methods=["POST", "GET"])
@login_required
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash(_("Пользователь %(username)s не найден.", username=username))
		return redirect(url_for("main.index"))
	if user == current_user:
		flash(_("Вы не можете подписаться сами на себя!"))
		return redirect(url_for("main.user", username=username))
	current_user.follow(user)
	db.session.commit()
	flash(_("Вы подписались на @%(username)s", username=username))
	return redirect(url_for("main.user", username=username))


@bp.route("/unfollow/<username>", methods=["POST", "GET"])
@login_required
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash(_("Пользователь %(username)s не найден.", username=username))
		return redirect(url_for("main.index"))
	if user == current_user:
		flash(_("Вы не можете отписаться сами от себя!"))
		return redirect(url_for("main.user", username=username))
	current_user.unfollow(user)
	db.session.commit()
	flash(_("Вы отписались от @%(username)s", username=username))
	return redirect(url_for("main.user", username=username))


@bp.route("/translate", methods=["POST"])
@login_required
def translate_text():
	return jsonify({"text": translate(request.form["text"],
									  request.form["source_language"],
									  request.form["dest_language"])})


@bp.route("/search")
@login_required
def search():
	if not g.search_form.validate():
		return redirect(url_for("main.explore"))
	page = request.args.get("page", 1, type=int)
	posts, total = Post.search(g.search_form.q.data, page,
							   current_app.config["POSTS_PER_PAGE"])
	next_url = url_for("main.search", q=g.search_form.q.data, page=page + 1) \
		if total > page * current_app.config["POSTS_PER_PAGE"] else None
	prev_url = url_for("main.search", q=g.search_form.q.data, page=page - 1) \
		if page > 1 else None
	return render_template("search.html", title=_("Поиск"), posts=posts,
						   next_url=next_url, prev_url=prev_url)


@bp.route("/avatar", methods=["GET", "POST"])
@login_required
def upload_file():
	if request.method == "POST":
		file = request.files["file"]
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join("/media/boris/Файлы/Код/fatolj/latest/app/avatars/", current_user.username + ".png"))
	return render_template("avatar.html")

@bp.route("/favicon.ico")
def fav():
	return send_file("/media/boris/Файлы/Код/fatolj/latest/app/static/favicon.ico")

@bp.route("/send_message/<recipient>", methods=["GET", "POST"])
@login_required
def send_message(recipient):
	user = User.query.filter_by(username=recipient).first_or_404()
	form = MessageForm()
	if form.validate_on_submit():
		msg = Message(author=current_user, recipient=user,
					  body=form.message.data)
		msga = Message(author=current_user, recipient=current_user, body="(сообщение было отправлено вами пользователю @" + str(user.username) + ") " + form.message.data)
		user.add_notification("unread_message_count", user.new_messages())
		db.session.commit()
		flash(_("Сообщение было отправлено"))
		return redirect(url_for("main.user", username=recipient))
	return render_template("send_message.html", title=_("Send Message"),
						   form=form, recipient=recipient)

@bp.route("/messages")
@login_required
def messages():
	current_user.last_message_read_time = datetime.utcnow()
	current_user.add_notification("unread_message_count", 0)
	db.session.commit()
	page = request.args.get("page", 1, type=int)
	messages = current_user.messages_received.order_by(
		Message.timestamp.desc()).paginate(
			page, current_app.config["POSTS_PER_PAGE"], False)
	next_url = url_for("main.messages", page=messages.next_num) \
		if messages.has_next else None
	prev_url = url_for("main.messages", page=messages.prev_num) \
		if messages.has_prev else None
	return render_template("messages.html", messages=messages.items,
						   next_url=next_url, prev_url=prev_url, path=request.full_path)

@bp.route("/notifications")
@login_required
def notifications():
	since = request.args.get("since", 0.0, type=float)
	notifications = current_user.notifications.filter(
		Notification.timestamp > since).order_by(Notification.timestamp.asc())
	return jsonify([{
		"name": n.name,
		"data": n.get_data(),
		"timestamp": n.timestamp
	} for n in notifications])

@bp.route("/share")
@login_required
def share():
	return render_template("share.html")

@bp.route("/getavatar/<username>")
def getavatar(username):
	return send_file("/media/boris/Файлы/Код/fatolj/latest/app/avatars/" + username + ".png")
