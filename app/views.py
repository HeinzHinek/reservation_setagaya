# -*- coding: utf-8 -*-
import json

from app import app, vacancy_checker
from flask import render_template


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/ajax/get_vacancies')
def get_vacancies():
    checker = vacancy_checker.VacancyChecker()
    data = checker.do_check()
    print data
    return json.dumps(data)
