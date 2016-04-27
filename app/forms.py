# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import PasswordField, SubmitField
from wtforms import validators


class LoginForm(Form):
    password = PasswordField(u'Password', [validators.data_required(),
                                           validators.length(min=5, max=30)])
    submit = SubmitField(u'Log in!')

