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
  # 有効か無効のフラグ
  is_active = db.Column(db.Boolean, unique=False, default=False)
  create_at = db.Column(db.DateTime, default=datetime.now) # 管理者用
  update_at = db.Column(db.DateTime, default=datetime.now) # テーブルの流れを確認する際に必要
  
  @classmethod # ユーザーをemailで絞り込み取得
  def select_user_by_email(cls, email):
    return cls.query.filter_by(email=email).first()


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