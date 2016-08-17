# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, g, redirect, session, flash, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logging
from logging.handlers import TimedRotatingFileHandler

from models import User, Report, Task

from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.datastructures import Headers

from datetime import datetime

from collections import OrderedDict

from StringIO import StringIO
from pyexcel_xlsx import save_data

import config


app = Flask(__name__, static_folder='static')
app.secret_key = config.secret_key

server_log = TimedRotatingFileHandler('server.log', 'D')
server_log.setLevel(logging.DEBUG)
server_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

error_log = TimedRotatingFileHandler('error.log', 'D')
error_log.setLevel(logging.ERROR)
error_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

app.logger.addHandler(server_log)
app.logger.addHandler(error_log)

engine = create_engine(config.sql_conn,
                       connect_args=config.sql_config['conn_args'],
                       echo=False)
Session = sessionmaker(bind=engine)


#########################################
# class InvalidUsage(Exception):
#     status_code = 400
#
#     def __init__(self, message, status_code=status_code):
#         Exception.__init__(self)
#         self.message = message
#         self.status_code = status_code
#
#
# @app.errorhandler(InvalidUsage)
# def invalid_usage(error):
#     response = make_response(error.message)
#     response.status_code = error.status_code
#     return response


@app.errorhandler(404)
def page_not_find(error):
    return render_template('error.html', error='page not find')


@app.errorhandler(403)
def request_forbidden(error):
    return render_template('error.html', error='request forbidden')


@app.before_request
def before_request():
    g.sql_session = Session()


@app.teardown_request
def teardown_request(exception):
    sql_session = getattr(g, 'sql_session', None)
    if sql_session is not None:
        sql_session.close()


@app.route('/')
def main():
    if session.get('user'):
        return redirect('/userHome')
    else:
        return render_template('index.html')


@app.route('/showSignIn')
def show_sign_in():
    return render_template('sign_in.html')


@app.route('/showSignUp')
def show_sign_up():
    return render_template('signup.html')


@app.route('/validateLogin', methods=['POST'])
def validate_login():
    _username = request.form['inputUserName']
    _password = request.form['inputPassword']

    try:
        user = g.sql_session.query(User).filter_by(username=_username).first()
    except Exception as e:
        return render_template('error.html', error=str(e))

    if user is None:
        return render_template('error.html', error="The user don't exists")

    if check_password_hash(user.password, _password):
        session['user'] = user.username
        session['name'] = user.name
        session['type'] = user.type

        return redirect('/userHome')

    else:
        return render_template('error.html', error="Account or password error")


@app.route('/signUp', methods=['POST'])
def sign_up():
    _name = request.form['inputName']
    _user_name = request.form['inputUserName']
    _password = request.form['inputPassword']

    username_list = g.sql_session.query(User.username).all()
    if _user_name not in username_list:
        user = User()
        user.name = _name
        user.username = _user_name
        user.password = generate_password_hash(_password)
        user.type = 1

        g.sql_session.add(user)

        try:
            g.sql_session.commit()
        except Exception as e:
            flash(str(e))
            g.sql_session.rollback()
            return redirect('/signUp')

        session['user'] = _user_name
        session['name'] = _name
        session['type'] = user.type
        return redirect('/userHome')

    else:
        flash("The duplicated username")
        return redirect('/signUp')


@app.route('/userHome')
def user_home():
    _username = session['user']
    report = get_last_report(_username)
    task = get_last_task(_username)
    try:
        user = g.sql_session.query(User).filter_by(username=_username).first()
    except Exception as e:
        return render_template('error.html', error=str(e))

    if user:
        return render_template('user_home.html', type=user.type, report=report, task=task)
    else:
        return render_template('error.html', error='Unauthorized Access')


def get_last_report(username):
    try:
        user_id = g.sql_session.query(User.id).filter_by(username=username).first().id
        g.sql_session.flush()
        reports = g.sql_session.query(Report).filter_by(user_id=user_id).order_by(Report.updated_time).all()
    except Exception as e:
        g.sql_session.callback()
        flash(str(e))
        return None

    if len(reports) > 0:
        report = reports[-1]
        if if_today(report.updated_time):
            return report
        else:
            return None
    else:
        return None


def if_today(updated_time):
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)

    return updated_time > today


def get_last_task(username):
    try:
        user_id = g.sql_session.query(User.id).filter_by(username=username).first().id
        g.sql_session.flush()
        tasks = g.sql_session.query(Task).filter_by(user_id=user_id).order_by(Task.updated_time).all()
    except Exception as e:
        flash(str(e))
        return None

    if len(tasks) > 0:
        task = tasks[-1]
        if if_today(task.updated_time):
            return task
        else:
            return None
    else:
        return None


@app.route('/createReport')
def show_report_form():
    return render_template('report_form.html', name=session.get('name'), report=get_last_report(session['user']))


@app.route('/saveReport', methods=['POST'])
def save_report():
    report = Report()

    report.user_id = g.sql_session.query(User).filter_by(username=session.get('user')).first().id
    report.system_name = request.form['inputName']
    report.status = request.form['inputStatus']
    report.bugs = request.form['inputBugs']
    report.updated_time = datetime.now()

    try:
        g.sql_session.add(report)
        g.sql_session.commit()
    except Exception as e:
        flash(str(e))

    return redirect('/userHome')


@app.route('/createDailyTask')
def show_task_form():
    return render_template('task_form.html', name=session.get('name'), task=get_last_report(session['user']))


@app.route('/saveTask', methods=['POST'])
def save_task():
    task = Task()

    task.user_id = g.sql_session.query(User).filter_by(username=session.get('user')).first().id
    task.completed = request.form['completed']
    task.uncompleted = request.form['uncompleted']
    task.coordination = request.form['coordination']
    task.updated_time = datetime.now()

    try:
        g.sql_session.add(task)
        g.sql_session.commit()
    except Exception as e:
        flash(str(e))

    return redirect('/userHome')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('name', None)
    session.pop('type', None)
    return redirect('/')


@app.route('/exportReport', methods=['GET'])
def export_reports():
    if session.get('type') != 2:
        return render_template('error.html', error="You are not authorized")

    data = [["系统名称", "负责人", "系统状态", "bug情况"]]

    for report in get_today_reports():
        user = g.sql_session.query(User).filter_by(id=report.user_id).first()
        data.append([report.system_name, user.name, report.status, report.bugs])

    return export({u'系统运行报告': data}, "系统运行报告.xlsx")


def get_today_reports():
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)

    try:
        reports = g.sql_session.query(Report).filter(Report.updated_time > today).all()
    except Exception as e:
        flash(str(e))
        return None

    return reports


def export(excel_dict, file_name):
    data = OrderedDict()
    data.update(excel_dict)
    io = StringIO()
    save_data(io, data)
    response = Response()
    response.status_code = 200
    response.data = io.getvalue()

    response_headers = Headers({
        'Pragma': "public",  # required,
        'Expires': '0',
        'Cache-Control': 'must-revalidate, post-check=0, pre-check=0',
        'Content-Type': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        'Content-Disposition': 'attachment; filename=\"%s\";' % file_name,
        'Content-Transfer-Encoding': 'binary',
        'Content-Length': len(response.data)
    })

    response.headers = response_headers
    return response


@app.route('/exportTask', methods=['GET'])
def export_tasks():
    if session.get('type') != 2:
        return render_template('error.html', error="You are not authorized")

    data = [["姓名", "今日工作", "待完成", "需协调"]]

    for task in get_today_tasks():
        user = g.sql_session.query(User).filter_by(id=task.user_id).first()
        data.append([user.name, task.completed, task.uncompleted, task.coordination])

    return export({u'日报': data}, "日报.xlsx")


def get_today_tasks():
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)

    try:
        tasks = g.sql_session.query(Task).filter(Task.updated_time > today).all()
    except Exception as e:
        flash(str(e))
        return None

    return tasks


@app.route('/reportList')
def report_list():
    reports = get_today_reports()
    result_list = []

    for report in reports:
        user = g.sql_session.query(User).filter_by(id=report.user_id).first()
        result_list.append((report, user))

    return render_template('report_list.html', list=result_list)


@app.route('/dailyTaskList')
def task_list():
    tasks = get_today_tasks()
    result_list = []

    for task in tasks:
        user = g.sql_session.query(User).filter_by(id=task.user_id).first()
        result_list.append((task, user))

    return render_template('task_list.html', list=result_list)


if __name__ == '__main__':
    app.run()
