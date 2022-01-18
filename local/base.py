from werkzeug.utils import redirect
from mailu import models, utils
from mailu.sso import sso, forms
from mailu.ui import access
import sys
import json

from flask import current_app as app
import flask
import flask_login

@sso.route('/login', methods=['GET', 'POST'])
def login():
    client_ip = flask.request.headers.get('X-Real-IP', flask.request.remote_addr)
    form = forms.LoginForm()
    form.submitAdmin.label.text = form.submitAdmin.label.text + ' Admin'
    form.submitWebmail.label.text = form.submitWebmail.label.text + ' Webmail'

    fields = []
    if str(app.config["WEBMAIL"]).upper() != "NONE":
        fields.append(form.submitWebmail)
    if str(app.config["ADMIN"]).upper() != "FALSE":
        fields.append(form.submitAdmin)
    fields = [fields]

    if form.validate_on_submit():
        if form.submitAdmin.data:
            destination = app.config['WEB_ADMIN']
        elif form.submitWebmail.data:
            destination = app.config['WEB_WEBMAIL']
        device_cookie, device_cookie_username = utils.limiter.parse_device_cookie(flask.request.cookies.get('rate_limit'))
        username = form.email.data
        if username != device_cookie_username and utils.limiter.should_rate_limit_ip(client_ip):
            flask.flash('Too many attempts from your IP (rate-limit)', 'error')
            return flask.render_template('login.html', form=form, fields=fields)
        if utils.limiter.should_rate_limit_user(username, client_ip, device_cookie, device_cookie_username):
            flask.flash('Too many attempts for this user (rate-limit)', 'error')
            return flask.render_template('login.html', form=form, fields=fields)
        user = models.User.login(username, form.pw.data)
        if user:
            flask.session.regenerate()
            flask_login.login_user(user)
            response = flask.redirect(destination)
            response.set_cookie('rate_limit', utils.limiter.device_cookie(username), max_age=31536000, path=flask.url_for('sso.login'), secure=app.config['SESSION_COOKIE_SECURE'], httponly=True)
            flask.current_app.logger.info(f'Login succeeded for {username} from {client_ip}.')
            return response
        else:
            utils.limiter.rate_limit_user(username, client_ip, device_cookie, device_cookie_username) if models.User.get(username) else utils.limiter.rate_limit_ip(client_ip)
            flask.current_app.logger.warn(f'Login failed for {username} from {client_ip}.')
            flask.flash('Wrong e-mail or password', 'error')
    return flask.render_template('login.html', form=form, fields=fields)

@sso.route('/proxy', methods=['GET'])
def proxy():
    client_ip = flask.request.headers.get('X-Real-IP', flask.request.remote_addr)
#    print(flask.request.headers.get('X-Auth-Email'), file = sys.stderr)
#    print(json.dumps(dict(flask.request.headers), indent=4), file = sys.stderr)
#    print(app.config['OPENRESTY_SECRET'], file = sys.stderr)
#    form = forms.LoginForm()
#    form.submitAdmin.label.text = form.submitAdmin.label.text + ' Admin'
#    form.submitWebmail.label.text = form.submitWebmail.label.text + ' Webmail'
    username=flask.request.headers.get('X-Auth-Email')
    secret=flask.request.headers.get('X-Auth-Proxy-Secret')

#    print(username, file = sys.stderr)
#    print(secret, file = sys.stderr)
#    print(secret==app.config['OPENRESTY_SECRET'], file = sys.stderr)

#    fields = []
#    if str(app.config["WEBMAIL"]).upper() != "NONE":
#        fields.append(form.submitWebmail)
#    if str(app.config["ADMIN"]).upper() != "FALSE":
#        fields.append(form.submitAdmin)
#    fields = [fields]

    destination = app.config['WEB_ADMIN']

    device_cookie, device_cookie_username = utils.limiter.parse_device_cookie(flask.request.cookies.get('rate_limit'))
    if username != device_cookie_username and utils.limiter.should_rate_limit_ip(client_ip):
        flask.flash('Too many attempts from your IP (rate-limit)', 'error')
        return flask.render_template('login.html', form=form, fields=fields)
    if utils.limiter.should_rate_limit_user(username, client_ip, device_cookie, device_cookie_username):
        flask.flash('Too many attempts for this user (rate-limit)', 'error')
        return flask.render_template('login.html', form=form, fields=fields)

    if not (app.config['OPENRESTY_SECRET'] in (None, '') or not app.config['PROXY_SECRET']) and app.config['PROXY_SECRET'] == secret and username != "":
#        print("tryin mail", file = sys.stderr)
        user = models.User.get(flask.request.headers.get('X-Auth-Email'))
        if user:
            flask.session.regenerate()
            flask_login.login_user(user)
            response = flask.redirect(destination)
            response.set_cookie('rate_limit', utils.limiter.device_cookie(username), max_age=31536000, path=flask.url_for('sso.login'), secure=app.config['SESSION_COOKIE_SECURE'], httponly=True)
            flask.current_app.logger.info(f'Login succeeded by proxy for {username} from {client_ip}.')
            return response
        else:
            utils.limiter.rate_limit_user(username, client_ip, device_cookie, device_cookie_username) if models.User.get(username) else utils.limiter.rate_limit_ip(client_ip)
            flask.current_app.logger.warn(f'Login failed by proxy for {username} from {client_ip}.')
            print(username, file = sys.stderr)
            flask.flash('Wrong e-mail or password', 'error')
    return flask.redirect(flask.url_for('.login'))

@sso.route('/logout', methods=['GET'])
@access.authenticated
def logout():
    flask_login.logout_user()
    flask.session.destroy()
    return flask.redirect(flask.url_for('.login'))

