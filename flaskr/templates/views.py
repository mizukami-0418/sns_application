# views.py
from flask import (
    Blueprint, abort, request, render_template,
    redirect, url_for, flash
)
from flask_login import login_user, login_required, logout_user
from flaskr.models import (User, PasswordResetToken)
from flaskr import db

from flaskr.forms import (
    LoginForm, RegisterForm
)
# Blueprintの作成
bp = Blueprint("app", __name__, url_prefix="")

# ホーム画面
@bp.route("/")
def home():
    return render_template("home.html")

# ログアウト
@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("app.home")) # ログアウトしたらホーム画面へ

# ログイン
@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)