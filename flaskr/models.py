# models.py
import secrets
from flaskr import db, login_manager
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_

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

    Returns:
      None

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

    Args:
      email (str): 検索するユーザーのメールアドレス.

    Returns:
      User or None: メールアドレスに一致するユーザーオブジェクト。見つからない場合はNone.

    """
    return cls.query.filter_by(email=email).first()
  
  def validate_password(self, password):
    """
      与えられたパスワードがユーザーのハッシュ化されたパスワードと一致するか検証するメソッド.

      Args:
        password (str): 検証するパスワード.

      Returns:
        bool: パスワードが一致する場合はTrue、それ以外はFalse.

    """
    return check_password_hash(self.password, password)
  
  def create_new_user(self):
    """
      ユーザーオブジェクトをデータベースに追加するメソッド.

      Returns:
        None

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

    Returns:
      None

    Example:
      user = User()
      user.save_new_password("my_secure_password")
      # インスタンスのパスワードがハッシュ化され、アクティブ状態が有効になります。
    """
    self.password = generate_password_hash(new_password)
    self.is_active = True
  
  # UserConnectとouterjoinで紐付ける
  @classmethod
  def search_by_name(cls, username):
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
    ).all()
    
  @classmethod
  def select_friends(cls):
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

      Returns:
        None

    """
    subject = 'パスワード設定用URL'
    body = f'パスワード設定用URL: http://127.0.0.1:5000/reset_password/{token}'
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

      Returns:
        None

      Example:
        User.delete_token("sample_token")
        トークンに対応するエントリがデータベースから削除されます。
    """
    cls.query.filter_by(token=str(token)).delete()
    db.session.commit()

class UserConnect(db.Model):
  
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
    self.from_user_id = from_user_id
    self.to_user_id = to_user_id
  
  def create_new_connect(self):
    db.session.add(self)
    
  @classmethod
  def select_by_from_user_id(cls, from_user_id):
    return cls.query.filter_by(
      from_user_id = from_user_id,
      to_user_id = current_user.get_id()
    ).first()
    
  def update_status(self):
    self.status = 2
    self.update_at = datetime.now()
    
  @classmethod
  def is_friend(cls, to_user_id):
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

class Message(db.Model):
  
  __tablename__ = 'messages'
  
  id = db.Column(db.Integer, primary_key=True)
  from_user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True
  )
  id = db.Column(db.Integer, primary_key=True)
  to_user_id = db.Column(
    db.Integer, db.ForeignKey('users.id'), index=True
  )
  is_read = db.Column(db.Boolean, default=False,)
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
  def get_friend_messages(cls, id1, id2):
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
    ).order_by(cls.id).all()