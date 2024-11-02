# ベースイメージとして Python 3.11 の軽量バージョンを使用
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係のファイルをコンテナにコピー
COPY requirements.txt /app/

# pipをアップグレードし、依存関係をインストール
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 残りのファイルをコンテナにコピー
COPY . /app

# アプリケーションを実行するコマンドを指定
CMD ["python", "app.py"]
