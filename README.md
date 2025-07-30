# モテメッセ API (LangChain専用)

FastAPIを使用したモテメッセのLangChain処理専用バックエンドAPI

## セットアップ

```bash
# 依存関係インストール
pipenv install

# 仮想環境を有効化
pipenv shell

# サーバー起動
python main.py
```

**注意**: データベース操作は`motemesse-front`リポジトリで管理されています。

## 技術スタック

- FastAPI
- Python 3.11
- Pipenv
- LangChain (TODO: 実装予定)
- JWT認証
- Pydantic

## ディレクトリ構造

```
.
├── main.py              # FastAPIメインファイル
├── Pipfile              # Python依存関係
├── service/
│   ├── app/
│   │   └── api/        # APIエンドポイント
│   │       ├── auth_routes.py      # 認証関連
│   │       ├── general_routes.py   # 一般的なエンドポイント
│   │       └── langchain_routes.py # LangChain処理エンドポイント
│   └── modules/        # 共通モジュール（認証ミドルウェア等）
└── .env.sample          # 環境変数サンプル
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