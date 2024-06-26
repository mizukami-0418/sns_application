# views.py
from datetime import datetime
from flask import (
  Blueprint, abort, request, render_template,
  redirect, url_for, flash, session, jsonify
)
from flask_login import login_user, login_required, logout_user, current_user
from flaskr.models import User, PasswordResetToken, UserConnect, TalkMessage, UserContact
from flaskr import db

from flaskr.forms import (
  LoginForm, RegisterForm, ResetPasswordForm, ForgotPasswordForm,
  UserForm, ChangePasswordForm, UserSearchForm, ConnectForm, MessageForm,
  ContactForm
)
from flask_mail import Mail, Message
from flaskr.utils.message_format import make_message_format, make_old_message_format

bp = Blueprint('app', __name__, url_prefix='')
mail = Mail()

@bp.route('/')
def home():
  """
  ホーム画面を表示するルート関数。

  Returns:
    HTML: ホーム画面のHTMLテンプレート。
  """
  friends = requested_friends = requesting_friends = None
  connect_form = ConnectForm()
  session['url'] = 'app.home'
  if current_user.is_authenticated:
    friends = User.select_friends()
    requested_friends = User.select_requested_friends()
    requesting_friends = User.select_requesting_friends()
  return render_template(
    'home.html', 
    friends = friends,
    requested_friends = requested_friends,
    requesting_friends = requesting_friends,
    connect_form = connect_form
  )

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
      flash(f'パスワードが間違っているよ。もう一度入力してみて！<br>もし忘れたら下のリンクからパスワードの再設定してね')
  # ログインが失敗したか、GETリクエストの場合はログイン画面を表示
  return render_template('login.html', form=form)

@bp.route('/register', methods=["GET", "POST"])
def register():
  """
  新しいユーザーを登録し、パスワードリセット用のトークンを生成してメールを送信します。

  このメソッドは新しいユーザーを登録し、パスワードリセットトークンを生成する。
  ユーザーに対しトークンを含むメールを送信します。
  メールにはパスワードリセット用のURLが含まれており、
  クリックすることで、パスワードをリセットできるようになります。

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
  パスワードを忘れた場合の処理をするエンドポイント。

  ユーザーがパスワードを忘れた場合、ここを通じてパスワードリセットの手続きを行います。
  メールアドレスがフォームに入力され、存在するユーザーであれば、
  パスワードリセット用のトークンを生成し、ユーザーにメールで送信します。

  Args: None

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
      
      flash(f'パスワード再設定用のURLをメールでお送りしました。\nリンク先より再設定をお願いします。')
      # ユーザーが存在しない場合
    else:
      flash('このメールアドレスのユーザーは存在しません')
  
  return render_template('forgot_password.html', form=form)

@bp.route('/user', methods=['GET', 'POST'])
@login_required
def user():
  """
  ユーザー情報編集を処理します。

  このルートは、ログイン済みユーザーが自分のユーザーページにアクセスし、ユーザー情報を表示および更新できるようにします。

  Args: None

  Returns:
    リクエストメソッドがGETなら:
      'user.html'テンプレートを描画し、ユーザーの情報を表示するためのUserFormを提供します。

    リクエストメソッドがPOSTでフォームが有効な場合:
      ログイン中のユーザーのIDを取得します。
      Userクラスの'select_user_by_id'メソッドを使用して、ユーザーIDに対応するユーザーを取得します。
      トランザクション内でユーザーのユーザー名とメールを更新します。
      フォームからアップロードされたユーザーのプロフィール画像を保存し、画像のパスをユーザーオブジェクトに設定します。
      データベースセッションをコミットし、フラッシュメッセージを表示します。

  Note:
    このルートはユーザーがログインしていることを要求します（@login_requiredでデコレートされています）。
  """
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
  """
  パスワード変更ページを処理します。

  このルートは、ログイン済みユーザーが自分のアカウントのパスワードを変更できるようにします。

  Args: None

  Returns:
    リクエストメソッドがGETなら:
      'change_password.html'テンプレートを描画し、パスワード変更用のChangePasswordFormを提供します。

      リクエストメソッドがPOSTでフォームが有効な場合:
        ログイン中のユーザーのIDを使用してユーザーオブジェクトを取得します。
        フォームから新しいパスワードを取得します。
        トランザクション内でユーザーオブジェクトに新しいパスワードを保存します。
        データベースセッションをコミットし、フラッシュメッセージを表示します。
        ユーザーのアカウントページにリダイレクトします。

  Note:
    このルートはユーザーがログインしていることを要求します（@login_requiredでデコレートされています）。

  Example:
    フォームを使用してパスワードを変更し、データベースにコミットすると、フラッシュメッセージが表示され、
    ユーザーはuser.htmlにリダイレクトされます。
  """
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

@bp.route('/user_search', methods=['GET'])
@login_required
def user_search():
  """
  ユーザー検索機能

  ログイン済みのユーザーがユーザー名で他のユーザーを検索できる。

  Args: None

  Returns:
    リクエストメソッドがGETなら:
      'user_search.html'テンプレートを描画し、入力用のUserSearchFormを提供します。

    リクエストメソッドがPOSTでフォームが有効な場合:
      提出されたフォームデータからユーザー名を取得します。
      Userクラスの'search_by_name'メソッドを呼び出して、提供されたユーザー名に一致するユーザーを取得します。
      'user_search.html'テンプレートを描画し、UserSearchFormと一致するユーザーのリストを提供します。

  Note:
    このルートはユーザーがログインしていることを要求します（@login_requiredでデコレートされています）。
  """
  form = UserSearchForm(request.form)
  connect_form = ConnectForm()
  session['url'] = 'app.user_search'
  users = None
  user_name = request.args.get('username', None, type=str)
  next_url = prev_url = None
  if user_name:
    page = request.args.get('page', 1, type=int)
    posts = User.search_by_name(user_name, page)
    next_url = url_for('app.user_search', page=posts.next_num, username=user_name) if posts.has_next else None
    prev_url = url_for('app.user_search', page=posts.prev_num, username=user_name) if posts.has_prev else None
    users = posts.items
    # UserテーブルとUserConnectテーブルを紐付け、statusを確認する
    # from 自分のID, to 相手のID, status=1:自分から申請中
    # to 自分のID, from 相手のID, status=1:相手から申請中
    # status=2:フレンド登録済み
    # レコードが存在しない場合はどちらでない
  return render_template(
    'user_search.html', form=form, connect_form=connect_form,
    users=users, next_url=next_url, prev_url=prev_url
  )

@bp.route('/connect_user', methods=['POST'])
@login_required
def connect_user():
  """
  ユーザー接続の処理を行う関数。

  ユーザー接続フォームからのPOSTリクエストを処理し、友達の接続やリクエストの受諾を行います。

  Returns:
    redirect: ユーザーを指定されたURLにリダイレクトします。
  """
  form = ConnectForm(request.form)
  if request.method == 'POST' and form.validate():
    if form.connect_condition.data == 'connect':
      new_connect = UserConnect(current_user.get_id(), form.to_user_id.data)
      with db.session.begin(nested=True):
        new_connect.create_new_connect()
      db.session.commit()
    elif form.connect_condition.data == 'accept':
      # 相手から自分へのUserConnectを取得
      connect = UserConnect.select_by_from_user_id(form.to_user_id.data)
      if connect:
        with db.session.begin(nested=True):
          connect.update_status() # statusを1から2へ更新
        db.session.commit()
  next_url = session.pop('url', 'app:home')
  return redirect(url_for(next_url))

@bp.route('/message/<id>', methods=['GET', 'POST'])
@login_required
def message(id):
  """
  メッセージの表示と送信を管理する関数。

  フレンドとのメッセージの表示、未読メッセージの更新、および新しいメッセージの送信を処理します。

  Args:
    id (int): メッセージの相手となるユーザーID。

  Returns:
    render_template or redirect: メッセージ画面の表示またはリダイレクトを行います。
  """
  if not UserConnect.is_friend(id):
    return redirect(url_for('app.home'))
  form = MessageForm(request.form)
  # フレンドのメッセージを取得
  messages = TalkMessage.get_friend_messages(current_user.get_id(), id)
  user = User.select_user_by_id(id)
  # 未読メッセージを取得
  read_message_ids = [message.id for message in messages if (not message.is_read) and (message.from_user_id == int(id))]
  not_checked_message_ids = [message.id for message in messages if message.is_read and (not message.is_checked) and (message.from_user_id == int(current_user.get_id()))]
  if not_checked_message_ids:
    # with db.session() as session:
    #   with session.begin_nested():
    #     TalkMessage.update_is_checked_by_id(not_checked_message_ids)
    # db.session.commit()
    with db.session.begin(nested=True):
      TalkMessage.update_is_checked_by_ids(not_checked_message_ids)
    db.session.commit()
  # read_message_idsのis_readをTrueに変更
  if read_message_ids:
    with db.session.begin(nested=True):
      TalkMessage.update_is_read_by_ids(read_message_ids)
    db.session.commit()
  if request.method == 'POST' and form.validate():
    new_message = TalkMessage(current_user.get_id(), id, form.message.data)
    with db.session.begin(nested=True):
      new_message.create_message()
    db.session.commit()
    return redirect(url_for('app.message', id=id)) # 保存したメッセージを取得
  return render_template(
    'message.html', form=form, messages=messages, to_user_id=id, user=user,
    # photo_image=photo_image
    )

@bp.route('/message_ajax', methods=['GET'])
@login_required
def message_ajax():
  """
  Ajaxリクエストに対する未読メッセージの処理を行う関数。

  Ajaxリクエストで送られたユーザーIDに対して、未読メッセージの取得、更新、および未チェックメッセージの処理を行います。

  Returns:
    jsonify: 未読メッセージと未チェックメッセージの情報をJSON形式で返します。
  """
  user_id = request.args.get('user_id', -1, type=int)
  # 未読メッセージを取得
  user = User.select_user_by_id(user_id)
  # 相手から自分への未読メッセージ
  not_read_messages = TalkMessage.select_not_read_messages(user_id, current_user.get_id())
  # 未読メッセージのidのみを取得
  not_read_message_ids = [message.id for message in not_read_messages]
  if not_read_message_ids:
    with db.session.begin(nested=True):
      TalkMessage.update_is_read_by_ids(not_read_message_ids)
    db.session.commit()
  # 自分の既読メッセージで未チェックを取得
  not_checked_messages = TalkMessage.select_not_checked_messages(current_user.get_id(), user.id)
  not_checked_message_ids = [not_checked_message.id for not_checked_message in not_checked_messages]
  if not_checked_message_ids:
    with db.session.begin(nested=True):
      TalkMessage.update_is_checked_by_ids(not_checked_message_ids)
    db.session.commit()
  return jsonify(data=make_message_format(user, not_read_messages), checked_message_ids = not_checked_message_ids)

@bp.route('/load_old_messages', methods=['GET'])
@login_required
def load_old_messages():
  """
  過去のメッセージの読み込みに関する処理を行う関数。

  Ajaxリクエストで送られたユーザーIDとオフセット値に基づいて、過去のメッセージを取得して返します。

  Returns:
    jsonify: 過去のメッセージの情報をJSON形式で返します。
  """
  user_id = request.args.get('user_id', -1, type=int)
  offset_value = request.args.get('offset_value', -1, type=int)
  if user_id == -1 or offset_value == -1:
    return
  messages = TalkMessage.get_friend_messages(current_user.get_id(), user_id, offset_value * 50)
  user = User.select_user_by_id(user_id)
  return jsonify(data=make_old_message_format(user, messages))

# お問い合わせを追加
@bp.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
  """
  お問い合わせページへのアクセスとお問い合わせフォームの処理を行うビュー関数

  Returns: response: お問い合わせフォームの処理結果に応じたレスポンス。

  Notes:
    - GETメソッド: お問い合わせフォームの表示。
    - POSTメソッド: フォームデータの検証およびデータベースへの保存を行う。
      保存後にユーザーへの通知メールを送信し、ホームページへリダイレクトする。
    """
  form = ContactForm()
  
  user_id = current_user.id
  username = current_user.username
  email = current_user.email
  inquiry = form.body.data
  if form.validate_on_submit():
    new_contact = UserContact(user_id=user_id, inquiry=inquiry)
    with db.session.begin(nested=True):
      new_contact.create_new_contact()
    db.session.commit()
    
    UserContact.send_contact_email(user_id, username, email, inquiry)
    flash(f'お問い合わせを受け付けました。\n1週間以内に登録メールアドレスへ返信いたします。')
    return redirect(url_for('app.home'))
  
  return render_template('contact.html', form=form)

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
  return redirect(url_for('app.token_list'))
# サンプルコネクト削除用コネクト一覧
@bp.route('/connects')
def connect_list():
  connects = UserConnect.query.all()
  return render_template('connect_list.html', connects=connects)
# サンプルコネクト削除用メソッド
@bp.route('/connects/<int:id>/delete', methods=['POST'])
def connect_delete(id):
  connect = UserConnect.query.get(id)
  db.session.delete(connect)
  db.session.commit()
  return redirect(url_for('app.connect_list'))
# ここまで
