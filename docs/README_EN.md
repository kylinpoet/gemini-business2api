<p align="center">
  <img src="../docs/logo.svg" width="120" alt="Gemini Business2API logo" />
</p>
<h1 align="center">Gemini Business2API</h1>
<p align="center">Empowering AI with seamless integration</p>
<p align="center">
  <a href="../README.md">简体中文</a> | <strong>English</strong>
</p>
<p align="center"><img src="https://img.shields.io/badge/License-CNC--1.0-red.svg" /> <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white" /> <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" /> <img src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white" /> <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white" /></p>

<p align="center">Convert Gemini Business to OpenAI-compatible API with multi-account load balancing, image generation, video generation, multimodal capabilities, and built-in admin panel.</p>

---

## 📜 License & Disclaimer

**License**: Cooperative Non-Commercial License (CNC-1.0) - See [LICENSE](../LICENSE) for details

### ⚠️ Prohibited Use & Anti-Abuse Policy

**This tool is strictly prohibited for:**
- Commercial use or profit-making activities
- Batch operations or automated abuse of any scale
- Market disruption or malicious competition
- Violations of Google's Terms of Service
- Violations of Microsoft's Terms of Service

**Consequences**: Violations may result in permanent account suspension and legal liability. All consequences are the sole responsibility of the user.

**Legitimate Use Only**: Personal learning, technical research, and non-commercial educational purposes only.

📖 **Full Disclaimer**: [DISCLAIMER_EN.md](DISCLAIMER_EN.md)

---

## ✨ Features

- ✅ Full OpenAI API compatibility - Seamless integration with existing tools
- ✅ Multi-account load balancing - Round-robin with automatic failover
- ✅ Multi-account configuration management - Batch import/export, status filtering, enable/disable, and in-panel editing
- ✅ Streaming output - Real-time responses
- ✅ Multimodal input - 100+ file types (images, PDF, Office docs, audio, video, code, etc.)
- ✅ Image generation & image-to-image - Configurable models, Base64 or URL output
- ✅ Video generation - Dedicated model with HTML/URL/Markdown output formats
- ✅ Smart file handling - Auto file type detection, supports URL and Base64
- ✅ Logging & monitoring - Real-time status and statistics
- ✅ Proxy support - Configure via admin settings panel
- ✅ Built-in admin panel - Online configuration and account management
- ✅ PostgreSQL / SQLite storage - Persistent accounts/settings/stats

## 🤖 Model Capabilities

| Model ID                 | Vision | Native Web | File Multimodal | Image Gen | Video Gen |
| ------------------------ | ------ | ---------- | --------------- | --------- | --------- |
| `gemini-auto`            | ✅      | ✅          | ✅               | Optional  | -         |
| `gemini-2.5-flash`       | ✅      | ✅          | ✅               | Optional  | -         |
| `gemini-2.5-pro`         | ✅      | ✅          | ✅               | Optional  | -         |
| `gemini-3-flash-preview` | ✅      | ✅          | ✅               | Optional  | -         |
| `gemini-3-pro-preview`   | ✅      | ✅          | ✅               | Optional  | -         |
| `gemini-3.1-pro-preview` | ✅      | ✅          | ✅               | Optional  | -         |
| `gemini-imagen`          | ✅      | ✅          | ✅               | ✅         | -         |
| `gemini-veo`             | ✅      | ✅          | ✅               | -         | ✅         |

> `gemini-imagen`: Dedicated image generation model · `gemini-veo`: Dedicated video generation model

---

## 🚀 Quick Start

### Method 1: Docker Compose (Recommended)

**Supports ARM64 and AMD64 architectures**

```bash
git clone https://github.com/Dreamy-rain/gemini-business2api.git
cd gemini-business2api
cp .env.example .env
# Edit .env to set ADMIN_KEY

docker compose up -d

# View logs
docker compose logs -f

# Update to latest version
docker compose pull && docker compose up -d
```

---

### Method 2: Setup Script

> **Prerequisites**: Git, Node.js & npm (for frontend build). Script auto-installs Python 3.11 and uv.

**Linux / macOS / WSL:**
```bash
git clone https://github.com/Dreamy-rain/gemini-business2api.git
cd gemini-business2api
bash setup.sh
# Edit .env to set ADMIN_KEY
source .venv/bin/activate
python main.py
# Background with pm2
pm2 start main.py --name gemini-api --interpreter ./.venv/bin/python3
```

**Windows:**
```cmd
git clone https://github.com/Dreamy-rain/gemini-business2api.git
cd gemini-business2api
setup.bat
# Edit .env to set ADMIN_KEY
.venv\Scripts\activate.bat
python main.py
# Background with pm2
pm2 start main.py --name gemini-api --interpreter ./.venv/Scripts/python.exe
```

The script handles: uv install, Python 3.11 download, dependency install, frontend build, `.env` creation.
To update, simply re-run the same script.

---

### Method 3: Manual Deployment

```bash
git clone https://github.com/Dreamy-rain/gemini-business2api.git
cd gemini-business2api

curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.11

cd frontend && npm install && npm run build && cd ..

uv venv --python 3.11 .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate.bat
uv pip install -r requirements.txt

cp .env.example .env
# Edit .env to set ADMIN_KEY
python main.py
```

---

### Access

- **Admin Panel**: `http://localhost:7860/` (Login with `ADMIN_KEY`)
- **API Endpoint**: `http://localhost:7860/v1/chat/completions`

---

## 🗄️ Database Persistence

By default, do not set `DATABASE_URL`. Use local SQLite (`data.db`) directly (recommended).
Use an online database only when necessary (for example: multi-instance shared data, or cloud platforms without persistent volume mounts).

**Configuration:**
- Local deployment → add to `.env`
- Cloud platforms → set in platform environment variables

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

**Online PostgreSQL (Optional):**

| Service | Free Tier | How to Get |
|---------|-----------|-----------|
| [Neon](https://neon.tech) | 512MB / 100 CPUH/month | Sign up → Create Project → Copy Connection string |
| [Aiven](https://aiven.io) | More generous | Sign up → Create PostgreSQL service → Copy connection string |

> Both `postgres://` and `postgresql://` formats are supported natively.

<details>
<summary>⚠️ FAQ: Periodic save failure / ConnectionDoesNotExistError</summary>

If you see errors like:

```
ERROR [COOLDOWN] Save failed: connection was closed in the middle of operation
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation
```

This happens when free PostgreSQL providers (e.g., Aiven free tier) close idle connections. **It does not affect normal usage** — the next operation will auto-reconnect. If frequent, consider switching to [Neon](https://neon.tech) or upgrading your database plan.

</details>

<details>
<summary>📦 Database Migration (Upgrading from older versions)</summary>

If you have legacy local files (`accounts.json` / `settings.yaml` / `stats.json`), run:

```bash
python scripts/migrate_to_database.py
```

The script auto-detects the environment (PostgreSQL / SQLite) and renames old files after migration.

</details>

---

## 📡 API Endpoints

Fully OpenAI API compatible. Works with ChatGPT-Next-Web, LobeChat, OpenCat, and other clients.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions (streaming supported) |
| `/v1/models` | GET | List available models |
| `/v1/images/generations` | POST | Image generation (text-to-image) |
| `/v1/images/edits` | POST | Image editing (image-to-image) |
| `/health` | GET | Health check |

**Example:**

```bash
curl http://localhost:7860/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

> `API_KEY` is configured in Admin Panel → System Settings. Leave empty for public access. Multiple keys supported (comma-separated).

---

## 🌐 Recommended Deployment Platforms

In addition to local Docker Compose, these platforms support Docker image deployment:

| Platform | Free Tier | Features |
|----------|-----------|----------|
| [Render](https://render.com) | ✅ Yes | Docker support, auto SSL, free PostgreSQL |
| [Railway](https://railway.app) | $5/month credit | One-click Docker deploy, built-in database |
| [Fly.io](https://fly.io) | ✅ Yes | Global edge deployment, persistent volumes |
| [Claw Cloud](https://claw.cloud) | ✅ Yes | Container cloud, simple and easy |
| Self-hosted VPS (Recommended) | — | Full control with Docker Compose |

> Docker image: `cooooookk/gemini-business2api:latest`
>
> Set `ADMIN_KEY` first. Configure `DATABASE_URL` only when needed (local `data.db` is the default recommendation).

### Zeabur Deployment Guide

1. Fork this repository to your GitHub
2. Log in to [Zeabur](https://zeabur.com) → **Create Project** → **Shared Cluster** → **Deploy New Service** → **Connect GitHub** → Select your forked repo
3. Add environment variables:

   | Variable | Required | Description |
   |----------|----------|-------------|
   | `ADMIN_KEY` | ✅ | Admin panel login key |
   | `DATABASE_URL` | Optional | PostgreSQL connection string (configure only when online DB is required) |

4. **Persistent Storage** (Important):

   Add persistent storage in service settings:

   | Disk ID | Mount Path |
   |---------|-----------|
   | `data` | `/app/data` |

5. Click **Redeploy** to apply settings

**Update**: GitHub repo → **Sync fork** → **Update branch**, Zeabur will auto-redeploy.

---

## 🌿 Mainline Focus

The current `main` / `beta` branches focus on the **Gemini Business 2API gateway** and the **admin panel**:

- `main`: stable line for production deployment
- `beta`: pre-release line where new features land first

Registration, refresh, and special proxy workflow experiments now live in dedicated branches or separate repositories instead of being part of the mainline README flow.

---

## 📸 Screenshots

### Admin System

<table>
  <tr>
    <td><img src="img/1.png" alt="Admin System 1" /></td>
    <td><img src="img/2.png" alt="Admin System 2" /></td>
  </tr>
  <tr>
    <td><img src="img/3.png" alt="Admin System 3" /></td>
    <td><img src="img/4.png" alt="Admin System 4" /></td>
  </tr>
  <tr>
    <td><img src="img/5.png" alt="Admin System 5" /></td>
    <td><img src="img/6.png" alt="Admin System 6" /></td>
  </tr>
</table>

### Image Effects

<table>
  <tr>
    <td><img src="img/img_1.png" alt="Image Effects 1" /></td>
    <td><img src="img/img_2.png" alt="Image Effects 2" /></td>
  </tr>
  <tr>
    <td><img src="img/img_3.png" alt="Image Effects 3" /></td>
    <td><img src="img/img_4.png" alt="Image Effects 4" /></td>
  </tr>
</table>

### Documentation

- Supported file types: [SUPPORTED_FILE_TYPES.md](SUPPORTED_FILE_TYPES.md)
- Refresh architecture and config boundaries: [refresh-architecture.md](../docs/refresh-architecture.md)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Dreamy-rain/gemini-business2api&type=date&legend=top-left)](https://www.star-history.com/#Dreamy-rain/gemini-business2api&type=date&legend=top-left)

**If this project helps you, please give it a ⭐ Star!**
