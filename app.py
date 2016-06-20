# coding=utf-8
from datetime import datetime

from flask import Flask, render_template, json, request, redirect, session
from models import User, Report
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import time
import sys


reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

engine = create_engine('mysql://root:123456@localhost/dailytask',connect_args={'charset':'utf8'},echo=False)
metadata = MetaData(engine)
Session = sessionmaker(bind=engine)
sql_session = Session()


@app.route("/")
def main():
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
        
        if user and check_password_hash(user.password, _password):
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

    if session.get('user'):
        return render_template('user_home.html', name=session.get('name'), report=report)
    else:
        return render_template('error.html', error='Unauthorized Access')


@app.route('/createReport')
def show_add_report():
    return render_template('report_form.html', name=session.get('name'), report=get_last_report())


@app.route('/saveReport', methods=['POST'])
def save_report():

    global sql_session

    user_id = sql_session.query(User).filter_by(username=session.get('user')).first().id
    name = request.form['inputName']
    status = request.form['inputStatus']
    bugs = request.form['inputBugs']
    updated_time = int(time.time())
    report = Report(user_id=user_id, system_name=name, status=status, bugs=bugs, updated_time=updated_time)
    sql_session.add(report)
    sql_session.commit()

    return redirect('/userHome')


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('name', None)
    return redirect('/')


def get_last_report():
    """get latest report"""
    global sql_session
    user_id = sql_session.query(User).filter_by(username=session.get('user')).first().id
    report_list = sql_session.query(Report).filter_by(user_id=user_id).order_by(Report.updated_time)

    report = None

    if report_list.first() is not None:
        report = report_list[-1]

    if report is not None and if_today(report.updated_time):
        return report
    else:
        return None


def if_today(updated_time):
    """
    if updated_time is in today
    :param updated_time:
    """
    today = datetime.today()
    today = datetime(today.year, today.month, today.day)
    last_update = datetime.fromtimestamp(updated_time)

    return last_update > today


if __name__ == "__main__":
    app.run()
