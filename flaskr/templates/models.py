# models.py　データモデルを定義
from flaskr import db, login_manager
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin

from datetime import datetime, timedelta
from uuid import uuid4


@login_manager.user_loader  # 特定のユーザーを取得するためのローダー
def load_user(user_id):
    return User.query.get(user_id)  # IDを元にDBからユーザーを取得して返す


class User(UserMixin, db.Model)  # UserMixinを継承し、認証に必要なメソッドを提供

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    # パスワードのハッシュを保存。デフォルトはsnsflaskappのハッシュが設定。
    password = db.Column(
        db.String(128),
        default=generate_password_hash("snsflaskapp")
    )
    picture_path = db.Column(db.Text) # プロフィール写真のファイルパスを保存
    # 有効か無効かのフラグ
    is_active = db.Column(db.Boolean, unique=False, default=False)
    create_at = db.Column(db.DateTime, default=datetime.now) # 作成日時
    update_at = db.Column(db.DateTime, default=datetime.now) # 更新日時


# パスワードリセット時に使用するトークンを管理
class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, Primary_key=True)
    token = db.Column(
        db.String(64),
        unique=True,
        index=True,
        server_default=str(uuid4)  # ランダムに値を生成し、文字列に変換しデフォルトにする
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expire_at = db.Column(db.DateTime, default=datetime.now) # トークンの有効期間
