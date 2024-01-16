# models.py
from flaskr import db, login_manager
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin

from datetime import datetime, timedelta
from uuid import uuid4

@login_manager.user_loader # userの情報を取得するための関数
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
      
  Class Methods:
      select_user_by_email: ユーザーをメールアドレスで絞り込んで取得するクラスメソッド。
      
  Methods:
      validate_password: パスワードの有効性を検証するメソッド。
  """
  __tablename__ = 'users'
  
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), index=True)
  email = db.Column(db.String(64), unique=True, index=True)
  password = db.Column(
    db.String(128),
    default = generate_password_hash('snsflaskapp') # デフォルトパスワード
  )
  picture_path = db.Column(db.Text)
  is_active = db.Column(db.Boolean, unique=False, default=False)
  create_at = db.Column(db.DateTime, default=datetime.now) # 管理者用
  update_at = db.Column(db.DateTime, default=datetime.now) # テーブルの流れを確認する際に必要
  
  def __init__(self, username, email):
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
    return cls.query.get(id)
  
  def save_new_password(self, new_password):
    self.password = generate_password_hash(new_password)
    self.is_active = True

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
    """PasswordResetToken インスタンスを初期化する。

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
    """指定されたユーザーに対して新しいパスワードリセットトークンを生成し、公開するメソッド。

    Args:
        user: User クラスのインスタンス。

    Returns:
        str: 生成されたパスワードリセットトークン。

    Example:
        user = User.query.get(1)  # 実際のユーザー取得ロジックに置き換える
        token = PasswordResetToken.publish_token(user)
    """
    token = str(uuid4()) # uuid4 を使用して一意のトークンを生成
    new_token = cls(
      token,
      user.id,
      datetime.now() + timedelta(minutes=15) # 有効期限を現在の時刻から15分後に設定
    )
    db.session.add(new_token) # 新しいトークンをデータベースセッションに追加
    return token # 生成されたトークンを返す
  
  @classmethod
  def get_user_id_by_token(cls, token):
    now = datetime.now()
    record = cls.query.filter_by(token=str(token)).filter(cls.expire_at > now).first()
    return record.user_id
  
  @classmethod
  def delete_token(cls, token):
    cls.query.filter_by(token=str(token)).delete()
    
    