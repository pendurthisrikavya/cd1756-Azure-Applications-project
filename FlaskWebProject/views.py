"""
Routes and views for the flask application.
"""

from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from datetime import datetime
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from FlaskWebProject.models import User, Post
from flask_login import current_user, login_user, logout_user, login_required
from config import Config
import uuid
import msal

# BLOB URL
imageSourceUrl = (
    f"https://{app.config['BLOB_ACCOUNT']}.blob.core.windows.net/"
    f"{app.config['BLOB_CONTAINER']}/"
)

# --------------------------
# HOME PAGE
# --------------------------
@app.route("/")
@app.route("/home")
@login_required
def home():
    posts = Post.query.all()
    return render_template("index.html", title="Home", posts=posts)


# --------------------------
# CREATE POST
# --------------------------
@app.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(
            form,
            request.files["image_path"],
            current_user.id,
            new=True,
        )
        return redirect(url_for("home"))

    return render_template(
        "post.html", title="Create Post", imageSource=imageSourceUrl, form=form
    )


# --------------------------
# EDIT POST
# --------------------------
@app.route("/post/<int:id>", methods=["GET", "POST"])
@login_required
def post(id):
    post = Post.query.get_or_404(id)
    form = PostForm(formdata=request.form, obj=post)

    if form.validate_on_submit():
        post.save_changes(form, request.files["image_path"], current_user.id)
        return redirect(url_for("home"))

    return render_template(
        "post.html",
        title="Edit Post",
        imageSource=imageSourceUrl,
        form=form,
    )


# --------------------------
# LOCAL LOGIN (USERNAME & PASSWORD)
# --------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    # Local login handling
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")

        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")
        return redirect(next_page)

    # Microsoft Login Setup
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(
        scopes=Config.SCOPE, state=session["state"]
    )

    return render_template(
        "login.html", title="Sign In", form=form, auth_url=auth_url
    )


# --------------------------
# MICROSOFT LOGIN CALLBACK
# --------------------------
@app.route(Config.REDIRECT_PATH)
def authorized():
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("login"))

    if "error" in request.args:
        return render_template("auth_error.html", result=request.args)

    if request.args.get("code"):
        cache = _load_cache()
        msal_app = _build_msal_app(cache)

        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"],
            scopes=Config.SCOPE,
            redirect_uri=url_for("authorized", _external=True, _scheme="https"),
        )

        if "error" in result:
            return render_template("auth_error.html", result=result)

        session["user"] = result.get("id_token_claims")

        # ALWAYS log in as admin for this project
        user = User.query.filter_by(username="admin").first()
        login_user(user)

        _save_cache(cache)

    return redirect(url_for("home"))


# --------------------------
# LOGOUT
# --------------------------
@app.route("/logout")
def logout():
    logout_user()

    if session.get("user"):
        session.clear()
        return redirect(
            Config.AUTHORITY
            + "/oauth2/v2.0/logout?post_logout_redirect_uri="
            + url_for("login", _external=True)
        )

    return redirect(url_for("login"))


# --------------------------
# MSAL UTILS
# --------------------------
def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID,
        authority=Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache,
    )


def _build_auth_url(authority=None, scopes=None, state=None):
    msal_app = _build_msal_app()
    return msal_app.get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=url_for("authorized", _external=True, _scheme="https"),
    )
