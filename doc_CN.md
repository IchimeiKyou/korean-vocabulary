# 韩语单词大师 — 技术文档

## 项目结构

```
korean-vocabulary/
├── main.py              # FastAPI 后端（API 端点）
├── database.py          # 数据库连接与初始化
├── models.py            # 数据库表定义（SQLAlchemy）
├── schemas.py           # 请求与响应结构定义（Pydantic）
├── requirements.txt     # Python 依赖包列表
├── render.yaml          # Render 部署配置
├── .python-version      # Python 版本锁定（3.11.12）
├── .gitignore
├── README.md
└── static/
    ├── index.html       # 前端单页应用（SPA）
    └── word_data.json   # 单词数据
```

---

## 各脚本说明

### `main.py` — FastAPI 后端

应用的核心逻辑，提供以下 API 端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/register` | 新用户注册 |
| POST | `/api/login` | 登录（每次登录更新地理位置） |
| GET | `/api/users/{username}` | 获取用户信息 |
| POST | `/api/users/{username}/sync` | 将学习进度同步到服务器（需 Basic 认证） |
| GET | `/api/leaderboard` | 获取排行榜（支持 `sort_by` 参数排序） |
| GET | `/api/health` | 服务器与数据库健康检查 |

**主要内部函数：**

- `parse_basic_auth(authorization)` — 解析 Basic 认证请求头，返回 `(username, password)` 元组
- `detect_location(request)` — 从请求 IP 地址获取地理位置信息（使用 `ipapi.co`）。本地 IP（如 `127.0.0.1`）直接返回空字符串
- `verify_user(username, authorization, db)` — 验证 Basic 认证，密码错误或用户不存在时返回 401/404

---

### `database.py` — 数据库连接与初始化

```python
DATABASE_URL = os.getenv("DATABASE_URL", "<默认连接字符串>")
```

- 优先读取环境变量 `DATABASE_URL`，否则使用默认的 Render PostgreSQL 连接
- 使用 `asyncpg` 驱动实现异步连接（`postgresql+asyncpg://`）
- `init_db()` — 应用启动时自动调用。若环境变量 `RESET_DB=true`，则先 DROP 所有表再重建（用于开发阶段重置数据）

---

### `models.py` — 表结构定义

使用 SQLAlchemy ORM 定义数据模型，目前只有一张 `users` 表。

---

### `schemas.py` — API 数据结构

使用 Pydantic 定义请求与响应的数据类型。

| 类名 | 用途 |
|------|------|
| `UserCreate` | 注册请求体（username、password、avatar_emoji） |
| `UserLogin` | 登录请求体（username、password） |
| `ProgressSync` | 进度同步请求体（words_mastered、words_learned、study_seconds、study_date） |
| `UserResponse` | 用户信息响应（不包含 password_hash） |
| `LeaderboardEntry` | 排行榜条目（包含 rank 字段） |

---

### `static/index.html` — 前端单页应用

除了与后端的 API 交互外，所有功能完全自包含。

**核心状态对象 `state` 字段说明：**

| 字段 | 说明 |
|------|------|
| `words` | 从 `word_data.json` 加载的全部单词 |
| `learnedIds` | 已学习单词 ID 的 Set（持久化到 localStorage） |
| `masteredIds` | 已掌握单词 ID 的 Set（持久化到 localStorage） |
| `unmasteredIds` | 未掌握单词 ID 的 Set（持久化到 localStorage） |
| `reviewQueue` | 当前学习会话的出题队列 |
| `user` | 当前登录用户的信息（来自服务器响应） |
| `credentials` | Basic 认证用的用户名/密码（仅存内存，不落地） |
| `levelFilter` | TOPIK 级别筛选（`'all'` / `'1'` / `'2'` / `'3'`） |
| `sessionMastered` / `sessionUnmastered` | 本次会话的答对/答错计数 |

**学习数据持久化策略：**
- 单词的学习状态（learned / mastered / unmastered）按用户名存入 `localStorage`（键名：`koreanVocab_{username}`）
- 学习时长、单词数等汇总数据同步到服务器数据库，触发时机为：会话结束时、每隔 2 分钟、页面关闭时

---

### `static/word_data.json` — 单词数据

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

| 字段 | 说明 |
|------|------|
| `id` | 单词 ID（从 0 开始） |
| `korean` | 韩语原文 |
| `romanization` | 罗马字注音 |
| `meaning` | 日语释义 |
| `level` | TOPIK 级别（1〜3） |
| `pos` | 词性（名詞、動詞、形容詞 等） |

---

## 数据库配置

### 连接信息

| 项目 | 内容 |
|------|------|
| 主机 | `dpg-d868ig9kh4rs73ck4ie0-a.oregon-postgres.render.com` |
| 数据库名 | `ranking_record` |
| 用户名 | `ranking_record_user` |
| 平台 | Render PostgreSQL（俄勒冈区域） |

外网连接字符串：
```
postgresql://ranking_record_user:0DMQwPfdf8oIA0ttdtlUS6QkNqYU6Ure@dpg-d868ig9kh4rs73ck4ie0-a.oregon-postgres.render.com/ranking_record
```

---

### `users` 表结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INTEGER (主键) | 自动递增 |
| `username` | VARCHAR(50) UNIQUE | 用户名（同时用作登录 ID 和显示名称） |
| `password` | VARCHAR(100) | 密码（明文存储） |
| `location` | VARCHAR(100) | 每次登录时由 IP 解析的地理位置（如 `Japan Tokyo`） |
| `avatar_emoji` | VARCHAR(10) | 用户选择的头像 Emoji |
| `total_study_seconds` | INTEGER | 累计学习总秒数 |
| `words_mastered` | INTEGER | 累计已掌握单词数 |
| `words_learned` | INTEGER | 累计已学习单词数 |
| `streak_days` | INTEGER | 连续学习天数 |
| `last_study_date` | VARCHAR(20) | 最后学习日期（ISO 格式：`YYYY-MM-DD`） |
| `created_at` | TIMESTAMPTZ | 注册时间（自动生成） |
| `updated_at` | TIMESTAMPTZ | 最后更新时间（自动维护） |

**设计说明：**
- 密码以明文存储（内部项目，便于管理员查看和找回）
- `location` 在每次登录时重新从 IP 查询并覆盖更新
- `words_mastered` / `words_learned` 由客户端直接上报 Set 的大小，服务器覆盖写入
- `total_study_seconds` 按会话秒数累加
- `streak_days` 由服务器根据 `last_study_date` 与当前日期的差值自动计算（相差 1 天则 +1，超过 1 天则重置为 1）

---

## 数据流向总览

```
浏览器（index.html）
    │
    ├─ 启动时：加载 word_data.json + 从 localStorage 恢复学习状态
    ├─ 登录/注册：POST /api/login 或 /api/register
    │       └─ 服务器根据 IP 获取地理位置，写入 users 表
    │
    ├─ 学习中：将 learned / mastered / unmastered 实时保存到 localStorage
    │
    └─ 同步触发时机（任意一种）：
            ├─ 会话结束时（showSessionComplete）
            ├─ 每隔 2 分钟（setInterval）
            └─ 页面关闭时（beforeunload）
                    └─ POST /api/users/{username}/sync（携带 Basic 认证）
                            └─ 更新 users 表中的学习统计数据
```
