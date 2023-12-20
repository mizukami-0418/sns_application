# __init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# login_managerの作成
login_manager = LoginManager()  # LoginManagerクラスからlogin_managerインスタンスを生成
login_manager.login_view = "app.view"  # リダイレクト先のエンドポイントを設定
login_manager.login_message = "ログインしてください"

# スクリプトのパスを取得し、絶対パスに変換する。
# これにより、basedirはアプリのルートディレクトリの絶対パスを表す。
# このパスを使用しデータベースファイルのパスを構築する。
basedir = os.path.abspath(os.path.dirname(__name__))
db = SQLAlchemy()
migrate = Migrate()


# Flaskアプリの設定とインスタンスを返す
def create_app():
    # Flaskアプリケーションの設定
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "mysite"  # 暗号化に使用する秘密鍵
    app.config["SQLALCHEMY_DATABASE_URI"] = \
        "sqlite:///" + os.path.join(basedir, "data.sqlite")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # トラッキング無効化
    # ブループリントの登録
    from flaskr.views import bp
    app.register_blueprint(bp)
    # 各種初期化
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    return app
