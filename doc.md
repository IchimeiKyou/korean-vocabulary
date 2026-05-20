# 韓国語単語マスター — 技術ドキュメント

## プロジェクト構成

```
korean-vocabulary/
├── main.py              # FastAPI バックエンド（APIエンドポイント）
├── database.py          # データベース接続・初期化
├── models.py            # データベーステーブル定義（SQLAlchemy）
├── schemas.py           # リクエスト・レスポンス定義（Pydantic）
├── requirements.txt     # Python 依存パッケージ
├── render.yaml          # Render デプロイ設定
├── .python-version      # Python バージョン固定（3.11.12）
├── .gitignore
├── README.md
└── static/
    ├── index.html       # フロントエンド SPA
    └── word_data.json   # 単語データ
```

---

## 各スクリプトの役割

### `main.py` — FastAPI バックエンド

アプリのコアロジック。以下のAPIエンドポイントを提供する。

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/register` | 新規ユーザー登録 |
| POST | `/api/login` | ログイン（毎回ロケーション更新） |
| GET | `/api/users/{username}` | ユーザー情報取得 |
| POST | `/api/users/{username}/sync` | 学習進捗をサーバーに同期（Basic認証必須） |
| GET | `/api/leaderboard` | ランキング取得（sort_by パラメータ対応） |
| GET | `/api/health` | サーバー・DB 死活確認 |

**主要な内部関数：**

- `parse_basic_auth(authorization)` — Basic 認証ヘッダーを解析し `(username, password)` を返す
- `detect_location(request)` — リクエストの IP アドレスから地理情報を取得（`ipapi.co` 使用）。ローカル IP（`127.0.0.1` など）の場合は空文字を返す
- `verify_user(username, authorization, db)` — Basic 認証の検証。パスワード不一致・ユーザー不存在で 401/404 を返す

---

### `database.py` — DB接続・初期化

```python
DATABASE_URL = os.getenv("DATABASE_URL", "<デフォルト接続文字列>")
```

- 環境変数 `DATABASE_URL` が設定されていればそれを使用、なければデフォルトの Render PostgreSQL に接続
- `asyncpg` ドライバを使った非同期接続（`postgresql+asyncpg://`）
- `init_db()` — アプリ起動時に実行。環境変数 `RESET_DB=true` の場合は全テーブルを DROP してから CREATE（開発リセット用）

---

### `models.py` — テーブル定義

SQLAlchemy の ORM モデル。`users` テーブル1つのみ定義。

---

### `schemas.py` — API スキーマ

Pydantic モデルによるリクエスト・レスポンスの型定義。

| クラス | 用途 |
|--------|------|
| `UserCreate` | 新規登録リクエスト（username, password, avatar_emoji） |
| `UserLogin` | ログインリクエスト（username, password） |
| `ProgressSync` | 進捗同期リクエスト（words_mastered, words_learned, study_seconds, study_date） |
| `UserResponse` | ユーザー情報レスポンス（password_hash は含まない） |
| `LeaderboardEntry` | ランキングエントリ（rank フィールド付き） |

---

### `static/index.html` — フロントエンド SPA

バックエンドへの依存以外はすべて自己完結した Single Page Application。

**主要な状態（`state` オブジェクト）：**

| フィールド | 説明 |
|-----------|------|
| `words` | `word_data.json` から読み込んだ全単語 |
| `learnedIds` | 学習済み単語 ID の Set（localStorage 保存） |
| `masteredIds` | マスター済み単語 ID の Set（localStorage 保存） |
| `unmasteredIds` | 未マスター単語 ID の Set（localStorage 保存） |
| `reviewQueue` | 現在のセッションの出題キュー |
| `user` | ログイン中のユーザー情報（サーバーレスポンス） |
| `credentials` | Basic 認証用の username/password（メモリのみ） |
| `levelFilter` | TOPIK レベルフィルタ（`'all'` / `'1'` / `'2'` / `'3'`） |
| `sessionMastered` / `sessionUnmastered` | セッション内の正誤カウント |

**学習データの永続化：**
- 単語の学習状態（learned/mastered/unmastered）は `localStorage` にユーザーごとに保存（キー: `koreanVocab_{username}`）
- 学習秒数・単語数などの集計はサーバーの DB に同期（セッション終了時・2分ごと・ページ離脱時）

---

### `static/word_data.json` — 単語データ

```json
[
  {
    "id": 0,
    "korean": "안녕하세요",
    "romanization": "annyeonghaseyo",
    "meaning": "こんにちは",
    "level": 1,
    "pos": "感嘆詞"
  },
  ...
]
```

| フィールド | 説明 |
|-----------|------|
| `id` | 単語 ID（0始まり） |
| `korean` | 韓国語 |
| `romanization` | ローマ字読み |
| `meaning` | 日本語の意味 |
| `level` | TOPIK レベル（1〜3） |
| `pos` | 品詞（名詞・動詞・形容詞 など） |

---

## データベース構成

### 接続情報

| 項目 | 値 |
|------|----|
| ホスト | `dpg-d868ig9kh4rs73ck4ie0-a.oregon-postgres.render.com` |
| データベース名 | `ranking_record` |
| ユーザー名 | `ranking_record_user` |
| プラットフォーム | Render PostgreSQL（Oregon リージョン） |

外部接続文字列：
```
postgresql://ranking_record_user:0DMQwPfdf8oIA0ttdtlUS6QkNqYU6Ure@dpg-d868ig9kh4rs73ck4ie0-a.oregon-postgres.render.com/ranking_record
```

---

### `users` テーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| `id` | INTEGER (PK) | 自動採番 |
| `username` | VARCHAR(50) UNIQUE | ユーザー名（表示名兼ログインID） |
| `password` | VARCHAR(100) | パスワード（平文保存） |
| `location` | VARCHAR(100) | ログイン時に IP から取得した地理情報（例: `Japan Tokyo`） |
| `avatar_emoji` | VARCHAR(10) | 選択したアバター絵文字 |
| `total_study_seconds` | INTEGER | 累計学習秒数 |
| `words_mastered` | INTEGER | マスター済み単語数（累計） |
| `words_learned` | INTEGER | 学習済み単語数（累計） |
| `streak_days` | INTEGER | 連続学習日数 |
| `last_study_date` | VARCHAR(20) | 最終学習日（ISO形式: `YYYY-MM-DD`） |
| `created_at` | TIMESTAMPTZ | 登録日時（自動） |
| `updated_at` | TIMESTAMPTZ | 最終更新日時（自動） |

**備考：**
- パスワードは平文で保存（内部プロジェクトのため）
- `location` はログインのたびに最新の IP から再取得して上書き更新
- `words_mastered` / `words_learned` はクライアントの Set サイズをそのまま上書き同期
- `total_study_seconds` はセッション秒数を累積加算
- `streak_days` はサーバー側で `last_study_date` との差分から自動計算（1日差 → +1、2日以上空き → リセット）

---

## データフロー概要

```
ブラウザ (index.html)
    │
    ├─ 起動時: word_data.json 読み込み + localStorage から学習状態復元
    ├─ ログイン/登録: POST /api/login or /api/register
    │       └─ サーバー側で IP→地理情報を取得し users テーブルに保存
    │
    ├─ 学習中: learned/mastered/unmastered を localStorage に随時保存
    │
    └─ 同期タイミング（以下のいずれか）:
            ├─ セッション完了時（showSessionComplete）
            ├─ 2分ごと（setInterval）
            └─ ページ離脱時（beforeunload）
                    └─ POST /api/users/{username}/sync (Basic認証)
                            └─ users テーブルを更新
```
