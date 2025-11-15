"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid
from FlaskWebProject import app


imageSourceUrl = 'https://'+ app.config['BLOB_ACCOUNT']  + '.blob.core.windows.net/' + app.config['BLOB_CONTAINER']  + '/'

@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get(int(id))
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            app.logger.warning(f"Invalid login attempt for username={form.username.data}")
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        app.logger.info(f"{user.username} logged in successfully via form login.")
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)

@app.route(Config.REDIRECT_PATH)  # Must match Redirect URI in Azure AD
def authorized():
    # Validate state (protection against CSRF)
    if request.args.get('state') != session.get("state"):
        app.logger.warning("State mismatch detected in MS login.")
        return redirect(url_for("home"))  

    # Handle login errors (if any)
    if "error" in request.args:
        app.logger.error(f"MS Login error: {request.args.get('error_description')}")
        return render_template("auth_error.html", result=request.args)

    # Handle successful auth code returned
    if request.args.get('code'):
        cache = _load_cache()
        msal_app = _build_msal_app(cache=cache)

        try:
            result = msal_app.acquire_token_by_authorization_code(
                request.args['code'],
                scopes=Config.SCOPE,
                redirect_uri=url_for("authorized", _external=True, _scheme='https')
            )
        except Exception as e:
            app.logger.error(f"MSAL authorization code exchange failed: {e}")
            return render_template("auth_error.html", result={"error": str(e)})

        # Handle if MSAL didn’t return a result
        if not result:
            app.logger.error("MS Login failed: No token received.")
            return render_template("auth_error.html", result={"error": "No token received."})

        # Handle MSAL errors
        if "error" in result:
            app.logger.warning(f"MS Login error: {result.get('error_description', 'Unknown error')}")
            return render_template("auth_error.html", result=result)

        # Success: store user info
        session["user"] = result.get("id_token_claims", {})
        app.logger.info(f"MS Login success: {session['user'].get('name', 'Unknown User')}")

        # Log in as admin (per your app design)
        user = User.query.filter_by(username="admin").first()
        if user:
            login_user(user)
            app.logger.info("Admin logged in successfully via MS Login.")
        else:
            app.logger.error("Admin user not found in database.")
            return render_template("auth_error.html", result={"error": "Admin user not found"})

        _save_cache(cache)

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    # Log which user is logging out (if any)
    if hasattr(current_user, "username") and current_user.is_authenticated:
        app.logger.info(f"{current_user.username} logged out.")
    else:
        app.logger.info("Anonymous user logged out or session ended.")

    logout_user()

    if session.get("user"):  # Used MS Login
        app.logger.info("MS user session cleared and redirected to Microsoft logout.")
        # Wipe out user and its token cache from session
        session.clear()
        # Also logout from your tenant's web session
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True))

    return redirect(url_for('login'))


def _load_cache():
    # TODO: Load the cache from msal, if it exists
    """Load token cache from session if it exists."""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    # TODO: Save the cache, if it has changed
    """Persist token cache back to session if changed."""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    # TODO: Return a ConfidentialClientApplication
    """Return a ConfidentialClientApplication instance from MSAL."""
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID,
        authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache
    )

def _build_auth_url(authority=None, scopes=None, state=None):
    msal_app = _build_msal_app(authority=authority)
    redirect_uri = url_for("authorized", _external=True, _scheme='https')
    app.logger.info(f"Redirecting to Microsoft with redirect_uri={redirect_uri}")
    return msal_app.get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=redirect_uri
    )

    # TODO: Return the full Auth Request URL with appropriate Redirect URI
