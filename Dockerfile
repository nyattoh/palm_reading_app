# ベースイメージとして Python 3.10 の軽量バージョンを使用
FROM python:3.10-slim

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係のファイルをコンテナにコピー
COPY requirements.txt /app/

# pipをアップグレードし、依存関係をインストール
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 残りのファイルをコンテナにコピー
COPY . /app

# アプリケーションを実行するコマンドを指定
CMD ["python", "app.py"]
