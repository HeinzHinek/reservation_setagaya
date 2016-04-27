# -*- coding: utf-8 -*-
import json

from flask import redirect, url_for, render_template, g, flash
from flask_login import login_required, current_user, login_user, logout_user

from app import app, vacancy_checker, lm
from forms import LoginForm
from config import login_password


class User:
    def __init__(self):
        self.id = 666

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3


@app.before_request
def before_request():
    g.user = current_user


@lm.user_loader
def load_user(user_id):
    return User()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        if password != login_password:
            flash(u"That's not the password you SOB!", 'alert-danger')
            return redirect(url_for('login'))
        login_user(User())

        flash(u"And you're logged in!")
        return redirect(url_for('index'))
    return render_template('login.html',
                           title=u'Login',
                           form=form)


@app.route('/logout')
def logout():
    logout_user()
    g.user = None
    return redirect(url_for('index'))


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/ajax/get_vacancies')
@login_required
def get_vacancies():
    checker = vacancy_checker.VacancyChecker()
    data = checker.do_check()
    return json.dumps(data)
