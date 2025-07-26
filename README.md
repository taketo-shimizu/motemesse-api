# モテメッセ API

FastAPIを使用したモテメッセのバックエンドAPI

## セットアップ

```bash
# 依存関係インストール
pipenv install

# 仮想環境を有効化
pipenv shell

# サーバー起動
python main.py
```

## 技術スタック

- FastAPI
- Python 3.11
- Pipenv
- PostgreSQL + pgvector
- JWT認証
- SQLAlchemy
- Pydantic

## ディレクトリ構造

```
service/
├── app/
│   ├── api/        # APIエンドポイント
│   └── database/   # データベース関連
└── modules/        # 共通モジュール
```

## 環境変数

`.env.sample`を`.env`にコピーして必要な値を設定してください。

## APIドキュメント

サーバー起動後、以下のURLでAPIドキュメントを確認できます：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 開発コマンド

```bash
pipenv run python main.py     # サーバー起動
pipenv run mypy .            # 型チェック
```