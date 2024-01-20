# views.py
from flask import (
  Blueprint, abort, request, render_template, redirect, url_for, flash
)
from flask_login import login_user, login_required, logout_user
from flaskr.models import User, PasswordResetToken
from flaskr import db

from flaskr.forms import LoginForm, RegisterForm, ResetPasswordForm, ForgotPasswordForm
from flask_mail import Message, Mail


bp = Blueprint('app', __name__, url_prefix='')
mail = Mail()

@bp.route('/')
def home():
  """
  ホーム画面を表示するルート関数。

  Returns:
      HTML: ホーム画面のHTMLテンプレート。

  """
  return render_template('home.html')

@bp.route('/logout')
def logout():
  """
  ログアウトを処理するルート関数。

  Returns:
      redirect: ログアウト後にホーム画面にリダイレクトする。

  """
  logout_user() # ログアウト実行
  return redirect(url_for('app.home')) # ログアウトしたらホーム画面へ

@bp.route('/login', methods=['GET', 'POST'])
def login():
  """
  ログインを処理するルート関数。

  Returns:
      HTML: ログイン画面のHTMLテンプレート。

  """
  form = LoginForm(request.form)
  if request.method == 'POST' and form.validate():
    # フォームから入力されたメールアドレスに一致するユーザーをデータベースから取得
    user = User.select_user_by_email(form.email.data)
    # ユーザーが存在し、アクティブであり、かつパスワードが正しい場合
    if user and user.is_active and user.validate_password(form.password.data):
      login_user(user, remember=True) # ユーザーをログイン状態にし、セッションに保存
      next_url = request.args.get('next', url_for('app.home'))
      # ログイン成功後に指定されたリダイレクト先URLにリダイレクト
      return redirect(next_url)
    elif not user: # ユーザーが存在しない場合
      flash('このユーザーは存在しません')
    elif not user.is_active: # ユーザーが存在するが無効な場合
      flash('無効なユーザーです。パスワードを再設定してください。')
    elif not user.validate_password(form.password.data):
      # ユーザーが存在し、アクティブであるが、パスワードが間違っている場合
      flash('パスワードが間違っています')
  # ログインが成功しなかった場合、またはGETリクエストの場合はログイン画面を表示
  return render_template('login.html', form=form)

@bp.route('/register', methods=["GET", "POST"])
def register():
  """
  ユーザー登録を処理するルート関数。

  Returns:
      HTML: ユーザー登録画面のHTMLテンプレート。

  """
  form = RegisterForm(request.form)
  if request.method == 'POST' and form.validate():
    user = User(
      username = form.username.data,
      email = form.email.data
    )
    with db.session.begin(subtransactions=True):
      user.create_new_user()
    db.session.commit()
    # パスワードリセットトークンを生成
    token = ''
    with db.session.begin(subtransactions=True):
      token = PasswordResetToken.publish_token(user)
    db.session.commit()
    
    # メールを送信
    send_password_reset_email(user.email, token)
    
    flash('パスワード設定用URLをお送りします。ご確認をお願いします。')
    # print(
    #   f'パスワード設定用URL:http://127.0.0.1:5000/reset_password/{token}'
    # )
    return redirect(url_for('app.login'))
  return render_template('register.html', form=form)

def send_password_reset_email(email, token):
    """
    パスワードリセット用のメールを送信する関数。

    Args:
        email (str): 送信先メールアドレス。
        token (str): パスワードリセット用トークン。

    Returns:
        None

    """
    subject = 'パスワード設定用URL'
    body = f'パスワード設定用URL: http://127.0.0.1:5000/reset_password/{token}'
    msg = Message(subject, recipients=[email], body=body)
    mail.send(msg)

@bp.route('/reset_password/<uuid:token>', methods=['GET', 'POST'])
def reset_password(token):
  """
  パスワードリセットを処理するルート関数。

  Args:
      token (uuid): パスワードリセットのトークン。

  Returns:
      HTML: パスワードリセット画面のHTMLテンプレート。

  """
  form = ResetPasswordForm(request.form)
  # PasswordResetTokenクラスのトークンからユーザーidを取得
  reset_user_id = PasswordResetToken.get_user_id_by_token(token)
  if not reset_user_id:
    abort(500) # 存在しない場合はHTTPステータスコードの500を返す
  if request.method == 'POST' and form.validate():
    password = form.password.data # 新しいパスワードの取得
    user = User.select_user_by_id(reset_user_id) # DBから対応するユーザーを取得
    # トランザクション内でDBとのセッションを開始
    with db.session.begin(subtransactions=True):
      user.save_new_password(password) # 新しいパスワードをユーザーオブジェクトに保存
      PasswordResetToken.delete_token(token) # トークンを使用して関連するパスワードリセットトークンを削除
    db.session.commit()
    flash('パスワードを更新しました')
    return redirect(url_for('app.login'))
  return render_template('reset_password.html', form=form)

@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
  form = ForgotPasswordForm(request.form)
  if request.method == 'POST' and form.validate():
    email = form.email.data
    user = User.select_user_by_email(email)
    if User:
      with db.session.begin(subtransactions=True):
        token = PasswordResetToken.publish_token(user)
      db.session.commit()
      reset_url = f'http://127.0.0.1:5000/reset_password/{token}'
      # メール送信用の関数を作成
    else:
      flash('このメールアドレスのユーザーは存在しません')
  return render_template('forgot_password.html', form=form)
