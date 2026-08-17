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

## Getting Started

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
