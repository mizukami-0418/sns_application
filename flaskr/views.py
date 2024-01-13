# views.py
from flask import (
  Blueprint, abort, request, render_template, redirect, url_for, flash
)
from flask_login import login_user, login_required, logout_user
from flaskr.models import User, PasswordResetToken
from flaskr import db

from flaskr.forms import LoginForm, RegisterForm

bp = Blueprint('app', __name__, url_prefix='')

@bp.route('/')
def home():
  return render_template('home.html')

@bp.route('/logout')
def logout():
  logout_user() # ログアウト実行
  return redirect(url_for('app.home')) # ログアウトしたらホーム画面へ

@bp.route('/login', methods=['GET', 'POST'])
def login():
  form = LoginForm(request.form)
