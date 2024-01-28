# views.py
from datetime import datetime
from flask import (
  Blueprint, abort, request, render_template, redirect, url_for, flash
)
from flask_login import login_user, login_required, logout_user, current_user
from flaskr.models import User, PasswordResetToken
from flaskr import db

from flaskr.forms import (
  LoginForm, RegisterForm, ResetPasswordForm, ForgotPasswordForm, UserForm, ChangePasswordForm
)
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
  # ログインが失敗したか、GETリクエストの場合はログイン画面を表示
  return render_template('login.html', form=form)

@bp.route('/register', methods=["GET", "POST"])
def register():
  """
    新しいユーザーを登録し、パスワードリセット用のトークンを生成してメールを送信します。

    このメソッドは新しいユーザーを登録し、パスワードリセットトークンを生成して、
    ユーザーに対してそのトークンを含むメールを送信します。ユーザーには
    パスワードリセット用のURLが含まれており、それをクリックすることでパスワード
    をリセットできるようになります。

  Args:
    self: インスタンス自体。
  
  Returns:
    flask.Response: ユーザーに通知を表示するためのリダイレクトレスポンス。
  """
  form = RegisterForm(request.form) # インスタンスを作成
  if request.method == 'POST' and form.validate(): # POSTメソッドかつバリデーション成功
    # formデータを利用して新規ユーザーを作成
    user = User(
      username = form.username.data,
      email = form.email.data
    )
    with db.session.begin(nested=True):
      # DBに新規ユーザーを登録
      user.create_new_user()
    db.session.commit()
    # パスワードリセットトークンを生成
    with db.session.begin(nested=True):
      token = PasswordResetToken.publish_token(user)
    db.session.commit()
    email = user.email
    # パスワード設定用URLをメールで送信
    PasswordResetToken.send_password_reset_email(email, token)
    
    flash('パスワード設定用URLをお送りします。ご確認をお願いします。')
    
  # バリデーションが失敗した場合、register.htmlを再度表示
  return render_template('register.html', form=form)

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
    with db.session.begin(nested=True):
      user.save_new_password(password) # 新しいパスワードをユーザーオブジェクトに保存
      PasswordResetToken.delete_token(token) # トークンを使用して関連するパスワードリセットトークンを削除
    db.session.commit()
      
    flash('パスワードを更新しました')
    
    return redirect(url_for('app.login'))
  return render_template('reset_password.html', form=form)

@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
  """
    パスワードを忘れた場合の処理を担当するエンドポイント。

    ユーザーがパスワードを忘れた場合、このエンドポイントを通じて
    パスワードリセットの手続きを行います。メールアドレスがフォームに
    入力され、存在するユーザーであれば、パスワードリセット用のトークン
    を生成し、ユーザーにメールで送信します。

    Args:
      None

    Returns:
      flask.Response: フォームの入力結果や処理結果に基づいたレスポンス。
  """
  # ForgotPasswordForm インスタンスの作成
  form = ForgotPasswordForm(request.form)
  if request.method == 'POST' and form.validate(): # POSTメソッドかつバリデーション成功
    email = form.email.data # フォームから入力されたメールアドレスを取得
    # 入力されたメールアドレスに対応するユーザーをDBから取得
    user = User.select_user_by_email(email)
    if user: # userが存在
      # パスワードリセットトークンを生成し、DBに保存
      with db.session.begin(nested=True):
        token = PasswordResetToken.publish_token(user)
      db.session.commit()
      
      # パスワードリセット用のメールをユーザーに送信
      PasswordResetToken.send_password_reset_email(email, token)
      
      flash('パスワード再設定用のURLをメールでお送りしました。\
            リンク先より再設定をお願いします。')
      # ユーザーが存在しない場合、エラーメッセージを表示
    else:
      flash('このメールアドレスのユーザーは存在しません')
  # フォームの入力結果や処理結果に基づいて、適切なテンプレートを表示
  return render_template('forgot_password.html', form=form)

@bp.route('/user', methods=['GET', 'POST'])
@login_required
def user():
  form = UserForm(request.form)
  if request.method == 'POST' and form.validate():
    user_id = current_user.get_id()
    user = User.select_user_by_id(user_id)
    with db.session.begin(nested=True):
      user.username = form.username.data
      user.email = form.email.data
      file = request.files[form.picture_path.name].read()
      if file:
        file_name = user_id + ' ' + \
          str(int(datetime.now().timestamp())) + '.jpg'
        picture_path = 'flaskr/static/user_image/' + file_name
        open(picture_path, 'wb').write(file)
        user.picture_path = 'user_image/' + file_name
    db.session.commit()
    flash('ユーザー情報を更新しました')
  return render_template('user.html', form=form)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
  form = ChangePasswordForm(request.form)
  if request.method == 'POST' and form.validate():
    user = User.select_user_by_id(current_user.get_id())
    password = form.password.data # 新しいパスワードの取得
    with db.session.begin(nested=True):
      user.save_new_password(password) # 新しいパスワードをユーザーオブジェクトに保存
    db.session.commit()
    flash('パスワードの更新を行いました')
    return redirect(url_for('app.user'))
  return render_template('change_password.html', form=form)

@bp.app_errorhandler(404)
def page_not_found(e):
  return redirect(url_for('app.home'))

@bp.app_errorhandler(500)
def server_error(e):
  return render_template('500.html'), 500


# サンプルデータ削除用ユーザー一覧
@bp.route('/users')
def user_list():
  users = User.query.all()
  return render_template('user_list.html', users=users)
# サンプルデータ削除用メソッド
@bp.route('/users/<int:id>/delete', methods=['POST'])
def user_delete(id):
  user = User.query.get(id)
  db.session.delete(user)
  db.session.commit()
  # with db.session.begin():
  #   User.query.filter_by(user.id).delete()
  # db.session.commit()
  return redirect(url_for('app.user_list'))
# サンプルデータ削除用トークン一覧
@bp.route('/tokens')
def token_list():
  tokens = PasswordResetToken.query.all()
  return render_template('token_list.html', tokens=tokens)
# サンプルトークン削除用メソッド
@bp.route('/tokens/<int:id>/delete', methods=['POST'])
def token_delete(id):
  token = PasswordResetToken.query.get(id)
  db.session.delete(token)
  db.session.commit()
  # with db.session.begin():
  #   User.query.filter_by(user.id).delete()
  # db.session.commit()
  return redirect(url_for('app.token_list'))
# ここまで
