# setup.py
# Flaskアプリのエントリーポイント
from flaskr import create_app

# create_app()関数を呼び出し、Flaskアプリのインスタンスを作成、変数appに割当
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
