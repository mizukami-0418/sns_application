# __init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'app.view'
login_manager.login_message = 'ログインをお願いします'

basedir = os.path.abspath(os.path.dirname(__name__))
db = SQLAlchemy()
migrate = Migrate()

def create_app():
  """
    Flaskアプリケーションを作成し、設定します。

    Returns:
        Flask: 設定されたFlaskアプリケーションのインスタンス。

    この関数はFlaskアプリケーションを初期化し、設定します。秘密鍵、データベースURIなどの
    必要な構成を行います。また、ブループリントを登録し、データベースを初期化し、データベース
    の変更をマイグレートし、ユーザー認証のためにログインマネージャーを設定します。

    設定が完了したFlaskアプリケーションのインスタンスが返されます。

    例:
        app = create_app()
        app.run(debug=True)
    """
  app = Flask(__name__)
  app.config['SECRET_KEY'] = 'mysite'
  app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  from flaskr.views import bp # viewsで定義するbpをインポート
  app.register_blueprint(bp)
  db.init_app(app)
  migrate.init_app(app, db)
  login_manager.init_app(app)
  return app
  