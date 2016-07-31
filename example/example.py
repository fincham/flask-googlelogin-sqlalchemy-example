import json

from flask import Flask, session, redirect, url_for, escape, request, render_template
from flask_googlelogin import GoogleLogin
from flask_login import UserMixin, login_required, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "this is the development key, don't use it for real"

# SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"

# Google keys for dev
# Obtain from https://console.developers.google.com
app.config['GOOGLE_LOGIN_CLIENT_ID'] = "long-random-string.apps.googleusercontent.com"
app.config['GOOGLE_LOGIN_CLIENT_SECRET'] = ""
app.config['GOOGLE_LOGIN_REDIRECT_URI'] = "http://127.0.0.1:5000/oauth2callback"

db = SQLAlchemy(app)
googlelogin = GoogleLogin(app)

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    google_id = db.Column(db.String(), unique=True)
    name = db.Column(db.String())
    avatar = db.Column(db.String())

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

@googlelogin.user_loader
def get_user(user_id):
    return User.query.filter_by(id=user_id).first()

@app.before_first_request
def before_first_request():
    db.create_all()

@app.route('/')
def index():
    return """<p><a href="%s">Log in with Google</p>""" % (
        googlelogin.login_url(),
    )

@app.route('/profile')
@login_required
def profile():
    return """
        <p>Hello, %s</p>
        <p><img src="%s" width="100" height="100"></p>
        <p>Token: %r</p>
        <p>Extra: %r</p>
        <p><a href="/logout">Logout</a></p>
    """ % (current_user.name, current_user.avatar, session.get('token'),
               session.get('extra'))

@app.route('/oauth2callback', methods=['GET', 'POST'])
@googlelogin.oauth2callback
def login(token, userinfo, **params):
    user = User.query.filter_by(google_id=userinfo['id']).first()

    if user:
        user.name = userinfo['name']
        user.avatar = userinfo['picture']
    else:
        user = User(google_id=userinfo['id'],
                    name=userinfo['name'],
                    avatar=userinfo['picture'])

    db.session.add(user)
    db.session.commit()

    login_user(user)
    session['token'] = json.dumps(token)
    session['extra'] = params.get('extra')
    return redirect(params.get('next', url_for('.profile')))


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return """
        <p>Logged out</p>
        <p><a href="/">Return to index</a></p>
    """

if __name__ == '__main__':
    app.run()
