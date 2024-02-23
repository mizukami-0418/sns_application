# models.py
import secrets
from flaskr import db, login_manager
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_, desc
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime, timedelta
from uuid import uuid4
from flask_mail import Message, Mail

mail = Mail()

# userの情報を取得するための関数
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id)) # Userクラスで定義したuserIDを取得

class User(UserMixin, db.Model):
  """
  ユーザーを表すデータベースモデルクラス。

  Attributes:
    id (int): ユーザーの一意の識別子。
    username (str): ユーザーのユーザー名。
    email (str): ユーザーのメールアドレス。
    password (str): ユーザーのハッシュ化されたパスワード。
    picture_path (str): ユーザーのプロフィール画像の保存先パス。
    is_active (bool): アカウントが有効か無効かを示すフラグ。
    create_at (datetime): ユーザーが作成された日時。
    update_at (datetime): ユーザー情報が最後に更新された日時。
  """
  __tablename__ = 'users'
  
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index=True)
  email = db.Column(db.String(64), unique=True, index=True)
  password = db.Column(
    db.String(128),
    default = generate_password_hash(secrets.token_urlsafe(16)) # デフォルトパスワード
  )
  picture_path = db.Column(db.Text)
  is_active = db.Column(db.Boolean, unique=False, default=False)
  create_at = db.Column(db.DateTime, default=datetime.now) # 管理者用
  update_at = db.Column(db.DateTime, default=datetime.now) # テーブルの流れを確認する際に必要
  
  def __init__(self, username, email):
    """
    クラスのインスタンスを初期化します。

    Args:
      self: インスタンス自体。
      username (str): ユーザーのユーザー名。
      email (str): ユーザーのメールアドレス。

    Returns: None

    Example:
      user = User("JohnDoe", "john@example.com")
      # インスタンスがユーザー名とメールアドレスで初期化されます。
    """
    self.username = username
    self.email = email

  @classmethod
  def select_user_by_email(cls, email):
    """
    メールアドレスに基づいてユーザーを絞り込み、取得するクラスメソッド.

    Args: email (str): 検索するユーザーのメールアドレス.

    Returns:
      User or None: メールアドレスに一致するユーザーオブジェクト。見つからない場合はNone.
    """
    return cls.query.filter_by(email=email).first()
  
  def validate_password(self, password):
    """
    与えられたパスワードがユーザーのハッシュ化されたパスワードと一致するか検証するメソッド.

    Args: password (str): 検証するパスワード.

    Returns:
      bool: パスワードが一致する場合はTrue、それ以外はFalse.
    """
    return check_password_hash(self.password, password)
  
  def create_new_user(self):
    """
    ユーザーオブジェクトをデータベースに追加するメソッド.

    Returns: None
    """
    db.session.add(self)
  
  @classmethod
  def select_user_by_id(cls, id):
    """
    ユーザーのIDを使用してデータベースからユーザーを取得します。

    Args:
      cls (User): クラス自体。
      user_id (int): 取得するユーザーのID。

    Returns:
      Userクラス or None: 指定されたIDのユーザーが見つかれば、Userクラスのインスタンスが返されます。見つからない場合はNoneが返されます。

    Example:
      user = User.select_user_by_id(123)
      if user:
        print(f"ユーザーが見つかりました: {user.username}")
      else:
        print("ユーザーが見つかりませんでした。")
    """
    return cls.query.get(id)
  
  def save_new_password(self, new_password):
    """
    新しいパスワードをハッシュ化して保存します。

    このメソッドは、与えられた新しいパスワードをハッシュ化し、
    インスタンスのパスワード属性に保存し、同時にアクティブ状態を有効にします。

    Args:
      self: インスタンス自体。
      new_password (str): ハッシュ化される新しいパスワード。

    Returns: None

    Example:
      user = User()
      user.save_new_password("my_secure_password")
      # インスタンスのパスワードがハッシュ化され、アクティブ状態が有効になります。
    """
    self.password = generate_password_hash(new_password)
    self.is_active = True
  
  # UserConnectとouterjoinで紐付ける
  @classmethod
  def search_by_name(cls, username, page=1):
    """
    ユーザー名で検索して一致するユーザーを返します。

    Args:username (str): 検索するユーザー名の一部または完全な文字列。

    Returns:
      list: 検索条件に一致するユーザーのリスト。各ユーザーはid、username、picture_pathの属性を持っています。

    Note:
      ユーザー名が指定された文字列を含む、かつ現在のログインユーザーのIDと異なり、
      かつアクティブなユーザーに対して検索が行われます。

    Example:
      User.search_by_name('John')  # 'John'を含むユーザー名で検索し、一致するユーザーのリストを返します。
    """
    user_connect1 = aliased(UserConnect) # from 検索相手のID,to ログインユーザーIDでUserConnectに紐付け
    user_connect2 = aliased(UserConnect) # to 検索相手のID,from ログインユーザーIDでUserConnectに紐付け
    return cls.query.filter(
      cls.username.like(f'%{username}%'),
      cls.id != int(current_user.get_id()),
      cls.is_active == True
    ).outerjoin(
      user_connect1,
      and_(
        user_connect1.from_user_id == cls.id, # 検索相手のID
        user_connect1.to_user_id == current_user.get_id() # ログインユーザーID
      )
    ).outerjoin(
      user_connect2,
      and_(
        user_connect2.from_user_id == current_user.get_id(),
        user_connect2.to_user_id == cls.id
      )
    ).with_entities(
      cls.id, cls.username, cls.picture_path,
      user_connect1.status.label("joined_status_to_from"),
      user_connect2.status.label("joined_status_from_to")
    ).order_by(cls.username).paginate(page=page, per_page=5, error_out=False)
    
  @classmethod
  def select_friends(cls):
    """
    クラスメソッド: select_friends()

    現在のユーザーと2度繋がりがある友達を取得します。ユーザーの友達関係はUserConnectモデルを介して確認されます。
    
    Returns:
      list: フレンドの情報を含むタプルのリスト。各タプルは (id, username, picture_path) の順で構成されます。
    """
    return cls.query.join(
      UserConnect,
      or_(
        and_(
          UserConnect.to_user_id == cls.id,
          UserConnect.from_user_id == current_user.get_id(),
          UserConnect.status == 2
        ),
        and_(
          UserConnect.from_user_id == cls.id,
          UserConnect.to_user_id == current_user.get_id(),
          UserConnect.status == 2
        )
      )
    ).with_entities(
      cls.id, cls.username, cls.picture_path
    ).all()
    
  @classmethod
  def select_requested_friends(cls):
    """
    クラスメソッド: select_requested_friends()

    現在のユーザーから友達リクエストが送られているユーザーを取得します。ユーザーの友達関係はUserConnectモデルを介して確認されます。
    
    Returns:
      list: リクエストが送られている友達の情報を含むタプルのリスト。各タプルは (id, username, picture_path) の順で構成されます。
    """
    return cls.query.join(
      UserConnect,
      and_(
        UserConnect.from_user_id == cls.id,
        UserConnect.to_user_id == current_user.get_id(),
        UserConnect.status == 1
      )
    ).with_entities(
      cls.id,  cls.username, cls.picture_path
    ).all()
  
  @classmethod  
  def select_requesting_friends(cls):
    """
    クラスメソッド: select_requesting_friends()

    現在のユーザーが送信した友達リクエストが保留中のユーザーを取得します。ユーザーの友達関係はUserConnectモデルを介して確認されます。
    
    Returns:
      list: リクエストが保留中の友達の情報を含むタプルのリスト。各タプルは (id, username, picture_path) の順で構成されます。
    """
    return cls.query.join(
      UserConnect,
      and_(
        UserConnect.from_user_id == current_user.get_id(),
        UserConnect.to_user_id == cls.id,
        UserConnect.status == 1
      )
    ).with_entities(
      cls.id,  cls.username, cls.picture_path
    ).all()
      
class PasswordResetToken(db.Model):
  """
  パスワードリセットトークンを表すデータベースモデルクラス。

  Attributes:
    id (int): トークンの一意の識別子。
    token (str): パスワードリセットのための一意のトークン。
    user_id (int): トークンが関連付けられているユーザーのID。
    expire_at (datetime): トークンの有効期限。
    create_at (datetime): トークンが作成された日時。
    update_at (datetime): トークン情報が最後に更新された日時。
  """
  
  __tablename__ = 'password_reset_tokens'
  
  id = db.Column(db.Integer, primary_key=True)
  token = db.Column(
    db.String(64),
    unique=True,
    index=True,
    default=lambda: str(uuid4) # uuidの値をランダムに生成
  )
  # usersテーブルと紐付ける外部キー
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  # expire_at = db.Column(db.DateTime, default=datetime.now) 下記に修正
  expire_at = db.Column(db.DateTime, default=lambda: datetime.now() + timedelta(days=1)) # トークン有効時間
  create_at = db.Column(db.DateTime, default=datetime.now)
  update_at = db.Column(db.DateTime, default=datetime.now)
  
  def __init__(self, token, user_id, expire_at):
    """
    PasswordResetToken インスタンスを初期化する。

    Args:
      token (str): リセットトークンの一意の識別子。
      user_id (int): リセットトークンに関連するユーザーID。
      expire_at (datetime): リセットトークンの有効期限。
    """
    self.token = token
    self.user_id = user_id
    self.expire_at = expire_at
  
  @classmethod
  def publish_token(cls, user):
    """
    指定されたユーザーに対して新しいパスワードリセットトークンを生成し、公開するメソッド。

    Args: 
      user: User クラスのインスタンス。

    Returns:
      str: 生成されたパスワードリセットトークン。

    Example:
      user = User.query.get(1)  # 実際のユーザー取得ロジックに置き換える
      token = PasswordResetToken.publish_token(user)
    """
    token = str(uuid4()) # 一意のトークンを生成
    new_token = cls(
      token,
      user.id,
      datetime.now() + timedelta(days=1) # 有効期限を現在の時刻から1日後に設定
    )
    db.session.add(new_token) # 新しいトークンをデータベースセッションに追加
    return token # 生成されたトークンを返す
  
  @classmethod
  def send_password_reset_email(cls, email, token):
    """
    パスワードリセット用のメールを送信する関数。

    Args:
      email (str): 送信先メールアドレス。
      token (str): パスワードリセット用トークン。

    Returns: None
    """
    subject = 'パスワード設定用URLを送信しました。本文より設定をお願いします。'
    body = f'パスワード設定用URLをお送りします。下記よりパスワードの設定をお願いします。\nパスワード設定用URL : http://127.0.0.1:5000/reset_password/{token}'
    msg = Message(subject, recipients=[email], body=body)
    mail.send(msg)
    
  @classmethod
  def get_user_id_by_token(cls, token):
    """
    トークンに対応するユーザーIDを取得。

    与えられたトークンが存在し、かつ有効期限が現在時刻よりも後である場合、
    トークンに対応するユーザーIDを返します。

    Args:
      cls (User): クラス自体。
      token (str): 検索対象のトークン。

    Returns:
      int or None: トークンに対応するユーザーIDが見つかれば返します。
        見つからない場合はNoneが返されます。

    Example:
      user_id = User.get_user_id_by_token("sample_token")
      if user_id:
        print(f"ユーザーID: {user_id}")
      else:
        print("ユーザーが見つかりませんでした。")
    """
    now = datetime.now()
    record = cls.query.filter_by(token=str(token)).filter(cls.expire_at > now).first()
    return record.user_id if record else None # recordがNoneでないことの確認
  
  @classmethod
  def delete_token(cls, token):
    """
    トークンに対応するデータベース内のエントリを削除します。

    Args:
      cls (User): クラス自体。
      token (str): 削除対象のトークン。

    Returns: None

    Example:
      User.delete_token("sample_token")
      トークンに対応するエントリがデータベースから削除されます。
    """
    cls.query.filter_by(token=str(token)).delete()
    db.session.commit()

class UserConnect(db.Model):
  """
  ユーザー接続情報を管理するデータベースモデルクラス。

  Attributes:
    id (int): ユーザー接続情報の一意の識別子として使用される主キー。
    from_user_id (int): 接続の発信元ユーザーのID。usersテーブルの外部キー。
    to_user_id (int): 接続の対象となるユーザーのID。usersテーブルの外部キー。
    status (int): 接続の状態を示すフラグ。1は申請中、2は承認済みを表す。
    create_at (DateTime): 接続情報の作成日時。デフォルトは現在の日時。
    update_at (DateTime): 接続情報の最終更新日時。デフォルトは現在の日時。
  """
  
  __tablename__ = 'user_connects'
  
  id = db.Column(db.Integer, primary_key=True)
  from_user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True
  )
  to_user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True
  )
  # 1が申請中、2が承認済み
  status = db.Column(db.Integer, unique=False, default=1)
  create_at = db.Column(db.DateTime, default=datetime.now)
  update_at = db.Column(db.DateTime, default=datetime.now)
  
  def __init__(self, from_user_id, to_user_id):
    """
    UserConnectクラスのインスタンスを初期化するコンストラクタ。

    Args:
      from_user_id (int): 接続の発信元ユーザーのID。
      to_user_id (int): 接続の対象となるユーザーのID。
    """
    self.from_user_id = from_user_id
    self.to_user_id = to_user_id
  
  def create_new_connect(self):
    db.session.add(self)
    
  @classmethod
  def select_by_from_user_id(cls, from_user_id):
    """
    from_user_idおよび現在のユーザーのIDに基づいてUserConnectのインスタンスを取得するクラスメソッド。

    Args: from_user_id (int): 取得する接続情報の発信元ユーザーのID。

    Returns:
      UserConnect or None: 指定された条件に一致するUserConnectのインスタンス。条件に一致するものがない場合はNone。
    """
    return cls.query.filter_by(
      from_user_id = from_user_id,
      to_user_id = current_user.get_id()
    ).first()
    
  def update_status(self):
    """
    UserConnectのステータスを更新し、最終更新日時を現在の日時に更新するメソッド。

    ステータスを2に設定し、更新が行われた時点の日時をupdate_at属性に設定します。
    """
    self.status = 2
    self.update_at = datetime.now()
    
  @classmethod
  def is_friend(cls, to_user_id):
    """
    指定されたユーザーが現在のユーザーと友達関係にあるかどうかを判定するクラスメソッド。

    Args: to_user_id (int): 判定対象のユーザーのID。

    Returns:
      bool: 指定されたユーザーが友達関係にある場合はTrue、それ以外の場合はFalse。
    """
    user = cls.query.filter(
      or_(
        and_(
          UserConnect.from_user_id == current_user.get_id(),
          UserConnect.to_user_id == to_user_id,
          UserConnect.status == 2
        ),
        and_(
          UserConnect.from_user_id == to_user_id,
          UserConnect.to_user_id == current_user.get_id(),
          UserConnect.status == 2
        )
      )
    ).first()
    return True if user else False

class TalkMessage(db.Model):
  """
  ユーザー間のメッセージ情報を管理するデータベースモデルクラス。

  Attributes:
    id (int): メッセージの一意の識別子として使用される主キー。
    from_user_id (int): メッセージの送信元ユーザーのID。usersテーブルの外部キー。
    to_user_id (int): メッセージの送信先ユーザーのID。usersテーブルの外部キー。
    is_read (bool): メッセージが既読されたかどうかを示すフラグ。デフォルトはFalse。
    is_checked (bool): メッセージが確認されたかどうかを示すフラグ。デフォルトはFalse。
    message (Text): メッセージの内容。
    create_at (DateTime): メッセージの作成日時。デフォルトは現在の日時。
    update_at (DateTime): メッセージの最終更新日時。デフォルトは現在の日時。
  """
  
  __tablename__ = 'messages'
  
  id = db.Column(db.Integer, primary_key=True)
  from_user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True
  )
  to_user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True
  )
  is_read = db.Column(db.Boolean, default=False)
  is_checked = db.Column(db.Boolean, default=False)
  message = db.Column(db.Text)
  create_at = db.Column(db.DateTime, default=datetime.now)
  update_at = db.Column(db.DateTime, default=datetime.now)
  
  def __init__(self, from_user_id, to_user_id, message):
    self.from_user_id = from_user_id
    self.to_user_id = to_user_id
    self.message = message
    
  def create_message(self):
    db.session.add(self)
    
  @classmethod
  def get_friend_messages(cls, id1, id2, offset_value=0, limit_value=50):
    """
    指定された2つのユーザー間でのメッセージを取得するクラスメソッド。

    Args:
      id1 (int): ユーザー1のID。
      id2 (int): ユーザー2のID。
      offset_value (int, optional): 取得開始位置のオフセット値。デフォルトは0。
      limit_value (int, optional): 取得するメッセージの上限数。デフォルトは50。

    Returns:
      list of TalkMessage: 指定された2つのユーザー間でのメッセージを時系列順に取得したリスト。
    """
    return cls.query.filter(
      or_(
        and_(
          cls.from_user_id == id1,
          cls.to_user_id == id2
        ),
        and_(
          cls.from_user_id == id2,
          cls.to_user_id == id1
        )
      )
    ).order_by(desc(cls.id)).offset(offset_value).limit(limit_value).all()
  
  @classmethod
  def update_is_read_by_ids(cls, ids):
    """
    指定されたメッセージIDのメッセージの既読状態を更新するクラスメソッド。

    Args: ids (list of int): 既読状態を更新するメッセージのIDリスト。

    Returns: None
    """
    cls.query.filter(cls.id.in_(ids)).update(
      { 'is_read': 1 },
      synchronize_session='fetch'
    )
  
  @classmethod
  def update_is_checked_by_ids(cls, ids):
    """
    指定されたメッセージIDのメッセージの確認状態を更新するクラスメソッド。

    Args: ids (list of int): 確認状態を更新するメッセージのIDリスト。

    Returns: None
    """
    cls.query.filter(cls.id.in_(ids)).update(
      { 'is_checked': 1 },
      synchronize_session='fetch'
    )
    
  @classmethod
  def select_not_read_messages(cls, from_user_id, to_user_id):
    """
    指定されたユーザー間で未読のメッセージを取得するクラスメソッド。

    Args:
      from_user_id (int): 未読メッセージの発信元ユーザーのID。
      to_user_id (int): 未読メッセージの受信先ユーザーのID。

    Returns: list of TalkMessage: 指定されたユーザー間で未読のメッセージを取得したリスト。
    """
    return cls.query.filter(
      and_(
        cls.from_user_id == from_user_id,
        cls.to_user_id == to_user_id,
        cls.is_read == 0
      )
    ).order_by(cls.id).all()
  
  @classmethod
  def select_not_checked_messages(cls, from_user_id, to_user_id):
    """
    指定されたユーザー間で未確認の既読メッセージを取得するクラスメソッド。

    Args:
      from_user_id (int): 未確認メッセージの発信元ユーザーのID。
      to_user_id (int): 未確認メッセージの受信先ユーザーのID。

    Returns: list of TalkMessage: 指定されたユーザー間で未確認の既読メッセージを取得したリスト。
    """
    return cls.query.filter(
      and_(
        cls.from_user_id == from_user_id,
        cls.to_user_id == to_user_id,
        cls.is_read == 1,
        cls.is_checked == 0
      )
    ).order_by(cls.id).all()

class UserContact(db.Model):
  
  __tablename__ = 'user_contacts'
  
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True, nullable=False
  )
  inquiry = db.Column(db.Text, nullable=False)
  create_at = db.Column(db.DateTime, default=datetime.now)
  update_at = db.Column(db.DateTime, default=datetime.now)
  
  def __init__(self, user_id, inquiry):
    self.user_id = user_id
    self.inquiry = inquiry
    
  # お問い合わせメールを送信する関数
  @classmethod
  def send_contact_email(cls, user_id, username, email, inquiry):
    # 送信先のメールアドレス
    recipient_email = 'ff10mm11yy23@yahoo.co.jp'
    
    # 件名の作成
    subject = f'{username}様からお問い合わせあり'
    # メールの本文にcurrent_userの情報を追加
    email_body = f'ユーザーID: {user_id}\n'
    email_body += f'ユーザー名: {username}\n'
    email_body += f'Email: {email}\n\n'
    email_body += f'問い合わせ内容:\n{inquiry}'

    # メールを作成
    msg = Message(subject=subject, recipients=[recipient_email], body=email_body)

    # メールを送信
    mail.send(msg)
  
  def create_new_contact(self):
    db.session.add(self)