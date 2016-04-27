# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

from flask_login import LoginManager
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = u'you need to be logged in dude...'


from app import views, forms

if __name__ == '__main__':
    app.run()
