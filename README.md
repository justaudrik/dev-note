# DevNote

> A full-stack, developer-oriented note-sharing platform with real-time collaborative editing, Markdown support, email verification, and secure document sharing.

Built as a full-stack software development project at the **University of Victoria**.

---

## Features

- **JWT Authentication** with email verification — accounts are only activated after clicking a verification link
- **Real-time collaborative editing** via WebSockets — multiple users can edit the same document simultaneously and see each other's changes keystroke-by-keystroke
- **Markdown + Plain Text** with a live split-pane preview that renders as you type
- **Document sharing** via unique expiring links and email invites — works across different networks and devices
- **Tag-based filtering** and full-text search across note titles and bodies
- **Note pinning** — pin important notes to the top of your list
- **Rate limiting** on all endpoints with stricter limits on auth routes
- **Email compatible with all domains** — supports Gmail, Outlook, Yahoo, SendGrid, and any SMTP provider
- **No frontend framework** — clean, responsive dark UI built in Vanilla HTML/CSS/JavaScript

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web Framework | FastAPI |
| Database | PostgreSQL (production) · SQLite (local dev) |
| ORM | SQLAlchemy |
| Authentication | JWT via `python-jose` + bcrypt via `passlib` |
| Real-Time | WebSockets (FastAPI built-in) |
| Email | SMTP via `smtplib` — Gmail, Outlook, Yahoo, SendGrid, custom |
| Markdown Parsing | marked.js (browser-side) |
| Frontend | Vanilla HTML · CSS · JavaScript |
| Deployment | Railway (Docker) |

---

## Getting Started — Local Development

### Prerequisites

- Python 3.12+
- `pip`
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/devnote.git
cd devnote
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in the following at minimum:

```env
JWT_SECRET=<run: python -c "import secrets; print(secrets.token_hex(32))">
```

SMTP settings are optional for local development. If you leave them blank, email verification still works — the server returns a direct verification link in the API response that you can follow without an email client.

### 4. Run the development server

```bash
python -m uvicorn app.main:app --reload
```

Open **http://localhost:8000** in your browser.

> The SQLite database (`devnote.db`) is created automatically on first run. No setup required.

### API Documentation

FastAPI auto-generates interactive API documentation at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Deployment — Railway

Railway is a cloud platform that handles PostgreSQL, WebSockets, and Docker natively. The following steps deploy DevNote publicly so that real-time collaboration and email sharing work between users on different devices and networks.

### Prerequisites

- Your project pushed to a **GitHub repository**
- A **Railway account** (railway.app — free tier available, sign up with GitHub)
- SMTP credentials (see `.env.example` for provider options)

---

### Step 1 — Push your code to GitHub

If you haven't already:

```bash
git init
git add .
git commit -m "feat: initial DevNote commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/devnote.git
git push -u origin main
```

> Make sure `.env` and `devnote.db` are listed in `.gitignore` — they must never be committed.

---

### Step 2 — Create a Railway project

1. Go to **railway.app** and sign in with GitHub
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Search for your `devnote` repository and click **Deploy Now**
5. Railway detects the `Dockerfile` automatically and starts building

---

### Step 3 — Add a PostgreSQL database

1. Inside your Railway project dashboard, click **+ New**
2. Select **Database → Add PostgreSQL**
3. Railway provisions a managed PostgreSQL instance and **automatically adds `DATABASE_URL`** to your project's environment — you do not need to set this manually

---

### Step 4 — Set environment variables

1. Click on your **DevNote service** (not the database) in the Railway dashboard
2. Go to the **Variables** tab
3. Add the following variables one by one:

| Variable | Value |
|---|---|
| `JWT_SECRET` | Run `python -c "import secrets; print(secrets.token_hex(32))"` and paste the result |
| `SMTP_HOST` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your email address |
| `SMTP_PASS` | Your app password (see `.env.example` for Gmail setup) |
| `SMTP_SSL` | `false` (use `true` only for port-465 providers) |
| `SMTP_FROM_NAME` | `DevNote` (or any display name you prefer) |
| `APP_URL` | Leave **blank** for now — you'll set this in Step 6 |

> `DATABASE_URL` is set automatically by Railway — do not add it manually.

---

### Step 5 — Wait for the first deployment to complete

1. Click on your DevNote service and go to the **Deployments** tab
2. Watch the build logs — the first build takes 1–2 minutes
3. Wait for the green **"Deploy succeeded"** status

---

### Step 6 — Set APP_URL

`APP_URL` tells DevNote what base URL to use in verification emails and share links.

1. In your DevNote service, go to **Settings → Domains**
2. Copy the Railway-provided domain (e.g. `https://devnote-production.up.railway.app`)
3. Go back to **Variables** and add:

```
APP_URL = https://devnote-production.up.railway.app
```

4. Railway automatically redeploys when a variable is added — wait for it to complete

---

### Step 7 — Test the live deployment

1. Visit your Railway URL in a browser
2. Register a new account — check your email for the verification link
3. Click the link to activate your account and land on the dashboard
4. Create a document, click **⇪ Share**, and send the link to another user on a different device
5. Both users should see each other's edits in real time

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET` | ✅ Production | dev fallback | Secret key for signing JWT tokens. Use a long random string in production. |
| `DATABASE_URL` | ✅ Production | SQLite | Set automatically by Railway PostgreSQL. Leave unset for local dev. |
| `APP_URL` | ✅ Production | auto-detected | Base URL used in email links. Set to your Railway URL after deploying. |
| `SMTP_HOST` | For email | — | SMTP server hostname |
| `SMTP_PORT` | For email | `587` | SMTP port (`587` for STARTTLS, `465` for SSL) |
| `SMTP_USER` | For email | — | SMTP login username (usually your email address) |
| `SMTP_PASS` | For email | — | SMTP password or app password |
| `SMTP_SSL` | For email | `false` | Set to `true` for port-465 direct SSL connections |
| `SMTP_FROM_NAME` | No | `DevNote` | Display name shown in the "From" field of sent emails |

---

## Project Structure

```
devnote/
├── app/
│   ├── main.py               # FastAPI app entry point — mounts routers + static files
│   ├── database.py           # SQLAlchemy engine — SQLite locally, PostgreSQL in production
│   ├── models.py             # User, Document, DocumentCollaborator, ShareLink
│   ├── schemas.py            # Pydantic schemas with email + field validation
│   ├── auth.py               # JWT creation/verification, bcrypt, get_current_user
│   ├── connection_manager.py # In-memory WebSocket connection tracker (per document)
│   ├── email_utils.py        # SMTP email sender — verification + share invite templates
│   ├── utils.py              # has_document_access() shared access helper
│   └── routers/
│       ├── auth_router.py    # /api/auth — register, verify, login, resend, me
│       ├── documents.py      # /api/documents — CRUD (owner + collaborator access)
│       └── collaboration.py  # /api/collab — share links, email invites + /ws WebSocket
├── static/
│   ├── index.html            # Login, register, and email verification flow
│   └── dashboard.html        # Main editor: documents, real-time collaboration, sharing
├── Dockerfile                # Used by Railway for cloud deployment
├── .dockerignore
├── .env.example              # Template — copy to .env and fill in values
├── .gitignore
└── requirements.txt
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create unverified account, send verification email |
| `GET` | `/api/auth/verify/{token}` | Verify email, return JWT |
| `POST` | `/api/auth/resend-verification` | Resend verification email |
| `POST` | `/api/auth/login` | Login, return JWT |
| `GET` | `/api/auth/me` | Get current user (protected) |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/documents/` | List owned + shared documents |
| `POST` | `/api/documents/` | Create a new document |
| `GET` | `/api/documents/{id}` | Get a single document |
| `PUT` | `/api/documents/{id}` | Update title, content, format, or pin status |
| `DELETE` | `/api/documents/{id}` | Delete a document (owner only) |

### Collaboration
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/collab/{id}/share` | Generate a shareable link |
| `POST` | `/api/collab/join/{token}` | Join a document via share link |
| `POST` | `/api/collab/{id}/invite` | Send an email invite |
| `GET` | `/api/collab/{id}/collaborators` | List collaborators |
| `WS` | `/ws/{id}?token={jwt}` | WebSocket — real-time collaborative editing |

---

## License

MIT — see [LICENSE](LICENSE) for details.
