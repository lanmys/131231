from flask import Flask, render_template, request, flash,redirect,url_for,session,g
import config
from models import User,Question,Answer
from exts import db
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy import or_

import os

DEBUG = True

SECRET_KEY = os.urandom(24)

HOSTNAME = '127.0.0.1'
PORT = '3306'
DATABASE = 'zlkt_demo'
USERNAME = 'root'
PASSWORD = 'root123456'
DB_URI = 'mysql+mysqldb://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOSTNAME,PORT,DATABASE)
#SQLALCHEMY_DATABASE_URI = DB_URI
#SQLALCHEMY_TRACK_MODIFICATIONS=False

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = '$'


#登录限制的装饰器

def login_required(func):

    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get('user_id'):
            return func(*args,**kwargs)
        else:
            return redirect(url_for('login'))
    return wrapper



@app.route('/')
def index():
    context = {
        'questions':Question.query.order_by('create_time').all()
    }
    return render_template('index.html',**context)

@app.route('/login/',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        telephone = request.form.get('telephone')
        password = request.form.get('password')
        user = User.query.filter(User.telephone==telephone).first()
        if user and user.check_password(password):
            rem = request.form.get('remember')
            if rem:
                session['user_id'] = user.id
            #如果你想再31天内都不需要登陆
                session.permanent = True
                return redirect(url_for('index'))
            else:
                session['user_id'] = user.id
                return redirect(url_for('index'))
        else:
            flash('电话或密码错误')
            return redirect(url_for('login'))


@app.route('/regist/',methods=['GET','POST'])
def regist():
    if request.method =='GET':
        return render_template('regist.html')
    else:
        telephone = request.form.get('telephone')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        #手机号码查重
        user = User.query.filter(User.telephone==telephone).first()
        if user:
            flash(r'该手机号码已经被注册')
        else:
            #进行密码验证
            if password2 != password1:
                flash(r'密码不相等')
                return redirect(url_for('regist'))
            else:
                user = User(telephone=telephone,username=username,password=password1)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))

@app.route('/forget/',methods=['GET','POST'])
def forget():
    if request.method == 'GET':
        return render_template('forget.html')
    else:
        telephone = request.form.get('telephone')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = User.query.filter(User.telephone==telephone,
                                 User.username==username).first()
        if user:
            if password2==password1:
                db.session.query(User).filter_by(telephone=telephone).update(
                    {'password':password2})
                db.session.commit()
                return redirect(url_for('login'))
            else:
                flash('前后密码不一致')
        else:
            flash('用户或者电话不存在')
            return redirect(url_for('forget'))



@app.route('/logout/')
def logout():
    #session.pop['user_id']
    #del session['user_id']
    session.clear()
    return redirect(url_for('login'))

@app.route('/question/',methods=['GET','POST'])
@login_required
def question():
    if request.method =='GET':
        return render_template('question.html')
    else:
        title = request.form.get('title')
        content = request.form.get('content')
        question = Question(title=title, content=content)
        user_id = session.get('user_id')
    #易错点：这里的user = db.session.query(User).get(user_id)不可以写为uer =
        # User.query.filter(User.id == user_id).first
        # 原因是这里从User里再次实例化了一个对象，即有两个session
        # flask 会报错
        user = db.session.query(User).get(user_id)
        question.author = user
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/detail/<question_id> ',methods=['GET','POST'])
@login_required
def detail(question_id):
    question_model = Question.query.filter(Question.id == question_id).first()
    return render_template('detail.html',question=question_model)

@app.route('/add_answer/',methods=['POST'])
@login_required
def add_answer():
    #return '跳转成功'

    content = request.form.get('answer_content')
    question_id = request.form.get('question_id')

    answer = Answer(content=content,question_id=question_id)
    user_id = session.get('user_id')
    user = db.session.query(User).get(user_id)
    answer.author = user
    question = db.session.query(Question).get(question_id) #易错点，视频给的是：
    # question= Question.query.filter(Question.id == question_id) 这里相当于再次创建了会话？
    answer.question = question
    db.session.add(answer)
    db.session.commit()
    return redirect(url_for('detail',question_id=question_id))
#1、app_context_processor作为一个装饰器修饰一个函数。
#2、函数的返回结果必须是dict，届时dict中的key将作为变量在所有模板中可见。



@app.route('/search/')
@login_required
def search():
    q = request.args.get('q')
    #或(or_) 需要导入sqlalchemy中的or_
    questions = Question.query.filter(or_(Question.title.contains(q),
                              Question.content.contains(q)))
    return render_template('index.html',questions=questions)

#
@app.before_request
def my_before_request():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter(User.id == user_id).first()
        if user:
            g.user = user


@app.context_processor
def my_context_processor():
    #判断当前用户是否处于登录状态
    '''
    if hasattr(g,'user'):
        :return {'user':g.user}
    :return {}
    '''
    user_id = session.get('user_id')
    if user_id :
        user = User.query.filter(User.id == user_id).first()
        if user:
            return {'user':user}
    return {}
if __name__ == '__main__':
    app.run(debug=True)