# coding=utf-8
from datetime import datetime

from flask import Flask, render_template, json, request, redirect, session
from models import User, Report, Task
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import time
import sys
from flask.ext import excel

reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

engine = create_engine('mysql://root:123456@123.57.58.91/dailytask',connect_args={'charset':'utf8'},echo=False)
metadata = MetaData(engine)
Session = sessionmaker(bind=engine)
sql_session = Session()


@app.route("/export", methods=['GET'])
def export_records():
    data = [["系统名称", "负责人", "系统状态", "bug情况"]]

    for report in get_today_reports():
        user = sql_session.query(User).filter_by(id=report.user_id).first()
        data.append([report.system_name, user.name, report.status, report.bugs])

    return excel.make_response_from_array(data, "csv",
                                          file_name="系统运行报告")


@app.route("/")
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
    try:
        _username = request.form['inputUserName']
        _password = request.form['inputPassword']

        global sql_session
        user = sql_session.query(User).filter_by(username=_username).first()
        print("enter")
        if user and check_password_hash(user.password, _password):
            print("enter if")
            session['user'] = user.username
            session['name'] = user.name
            return redirect('/userHome')
        else:
            return render_template('error.html', error="用户名或密码错误")

    except Exception as e:
        print(e)
        return render_template('error.html', error=str(e))


@app.route('/signUp', methods=['POST'])
def sign_up():
    # read the posted values from the UI
    _name = request.form['inputName']
    _user_name = request.form['inputUserName']
    _password = request.form['inputPassword']

    # validate the received values
    if _name and _user_name and _password:

        _hashed_password = generate_password_hash(_password)

        try:
            global engine
            conn = engine.raw_connection()
            cursor = conn.cursor()
            cursor.callproc('sp_createUser', (_name, _user_name, _hashed_password))
            data = cursor.fetchall()
            cursor.close()

            if len(data) is 0:
                conn.commit()
                session['user'] = _user_name
                session['name'] = _name
                return redirect('/userHome')
            else:
                return render_template('error.html', error="user already exists")

        except Exception as e:
            print(e)
            return render_template('error.html', error=str(e))


@app.route('/userHome')
def user_home():
    report = get_last_report()
    task = get_last_task()
    user = sql_session.query(User).filter_by(username=session['user']).first()

    if user:
        return render_template('user_home.html', type=user.type, report=report, task=task)
    else:
        return render_template('error.html', error='Unauthorized Access')


@app.route('/reportList')
def report_list():
    reports = get_today_reports()
    result_list = []

    for report in reports:
        user = sql_session.query(User).filter_by(id=report.user_id).first()
        result_list.append((report, user))

    return render_template('report_list.html', list=result_list)


@app.route('/createReport')
def show_report_form():
    return render_template('report_form.html', name=session.get('name'), report=get_last_report())


@app.route('/saveReport', methods=['POST'])
def save_report():
    global sql_session
    try:
        user_id = sql_session.query(User).filter_by(username=session.get('user')).first().id
        name = request.form['inputName']
        status = request.form['inputStatus']
        bugs = request.form['inputBugs']
        updated_time = datetime.now()
        report = Report(user_id=user_id, system_name=name, status=status, bugs=bugs, updated_time=updated_time)
        sql_session.add(report)
        sql_session.commit()
    except Exception as e:
        print(e)
        sql_session.rollback()

    return redirect('/userHome')


@app.route('/dailyTaskList')
def task_list():
    tasks = get_today_tasks()
    result_list = []

    for task in tasks:
        user = sql_session.query(User).filter_by(id=task.user_id).first()
        result_list.append((task, user))

    return render_template('task_list.html', list=result_list)


@app.route('/createDailyTask')
def show_task_form():
    return render_template('task_form.html', name=session.get('name'), task=get_last_task())


@app.route('/saveTask', methods=['POST'])
def save_task():
    global sql_session
    try:
        user_id = sql_session.query(User).filter_by(username=session.get('user')).first().id
        completed = request.form['completed']
        uncompleted = request.form['uncompleted']
        coordination = request.form['coordination']
        updated_time = datetime.now()
        task = Task(user_id=user_id, completed=completed, uncompleted=uncompleted, coordination=coordination,
                    updated_time=updated_time)
        sql_session.add(task)
        sql_session.commit()
    except Exception as e:
        print(e)
        sql_session.rollback()

    return redirect('/userHome')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('name', None)
    return redirect('/')


def get_last_report():
    """get latest report"""
    print(session.get('user'))
    global sql_session
    try:
        user_id = sql_session.query(User).filter_by(username=session.get('user')).first().id
        reports = sql_session.query(Report).filter_by(user_id=user_id).order_by(Report.updated_time)
        report = None

        if reports.first() is not None:
            report = reports[-1]

        if report is not None and if_today(report.updated_time):
            return report
        else:
            return None

    except Exception as e:
        sql_session.rollback()
        print(e)
        return None


def get_last_task():
    """get latest daily task"""
    global sql_session
    try:
        user_id = sql_session.query(User).filter_by(username=session.get('user')).first().id
        tasks = sql_session.query(Task).filter_by(user_id=user_id).order_by(Task.updated_time)
        task = None

        if tasks.first() is not None:
            task = tasks[-1]

        if task is not None and if_today(task.updated_time):
            return task
        else:
            return None

    except Exception as e:
        sql_session.rollback()
        print(e)
        return None


def get_today_reports():
    """get reports created today"""
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)

    global sql_session
    reports = sql_session.query(Report).filter(Report.updated_time > today)
    return reports


def get_today_tasks():
    """get tasks created today"""
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)

    global sql_session
    tasks = sql_session.query(Task).filter(Task.updated_time > today)
    return tasks


def if_today(updated_time):
    """
    if updated_time is in today
    :param updated_time:
    """
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)

    return updated_time > today


if __name__ == "__main__":
    app.run()
