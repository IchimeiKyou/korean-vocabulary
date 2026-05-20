# 한국어 단어 마스터 (Korean Vocabulary Master)

多人在线韩语单词学习应用，支持背单词、学习进度追踪和排行榜。

## 功能

- **单词学习**: 卡片式韩语单词记忆（含韩文、罗马音、词性、TOPIK 等级、中文释义）
- **学习/复习模式**: 新词学习 + 智能复习（自动混入已掌握单词巩固记忆）
- **用户系统**: 注册/登录、头像选择、个人信息管理
- **进度追踪**: 学习时长、掌握单词数、连续学习天数
- **排行榜**: 多维度排名（掌握数 / 学习数 / 时长 / 连续天数）

## 技术栈

- **前端**: 纯 HTML/CSS/JS 单页应用
- **后端**: Python FastAPI
- **数据库**: PostgreSQL (asyncpg)
- **部署**: Render

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 设置数据库 URL（或使用默认值）
export DATABASE_URL="postgresql://..."

# 启动开发服务器
uvicorn main:app --reload --port 8000
```

访问 http://localhost:8000

## 部署到 Render

1. 将代码推送到 GitHub 仓库
2. 在 Render 中创建新 Web Service
3. 连接 GitHub 仓库
4. Render 会自动读取 `render.yaml` 配置
5. 或手动设置:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - 环境变量: `DATABASE_URL`

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/users` | 注册新用户 |
| GET | `/api/users/{username}` | 获取用户信息 |
| PATCH | `/api/users/{username}` | 更新用户信息 |
| POST | `/api/users/{username}/sync` | 同步学习进度 |
| GET | `/api/leaderboard?sort_by=&limit=` | 获取排行榜 |

## 键盘快捷键

| 按键 | 功能 |
|------|------|
| 空格 | 显示/隐藏释义 |
| 1 / ← | 标记为不认识 |
| 2 / → | 标记为认识 |
