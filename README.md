# DevBoard

A backend API for managing projects, sprints, and issues — similar to Jira or Linear. Built as a learning project to understand how production backend systems are structured.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## What it does

- Users can register, log in, and manage their profile
- Create projects and invite team members with roles (Admin, Developer, Viewer)
- Create issues with priority, type, status, assignee, labels and story points
- Organise issues into sprints
- Comment on issues
- Get real-time updates via WebSockets when teammates make changes
- Project stats are cached in Redis to avoid repeated database queries
- Email notifications are sent in the background via Celery when an issue is assigned

---

## Architecture

Two separate services that share a Redis instance:

```
Client
  ├── REST API calls  →  Django (port 8000)
  └── WebSocket       →  FastAPI (port 8001)

Django  →  PostgreSQL (main database)
Django  →  Redis (caching + Celery broker)
FastAPI →  Redis (real-time events + pub/sub)
Celery  →  Redis (task queue)
```

I split the project into two services because Django is great for data-heavy REST APIs with its ORM and admin panel, while FastAPI handles async WebSocket connections more efficiently. They communicate through a shared Redis layer rather than calling each other directly.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Core API | Django + DRF | ORM, admin panel, mature ecosystem |
| Real-time | FastAPI | Async, WebSocket support, fast |
| Database | PostgreSQL (Neon) | Relational, reliable, free tier |
| Cache + Broker | Redis | Fast in-memory, pub/sub support |
| Background Jobs | Celery | Async task processing |
| Auth | JWT (SimpleJWT) | Stateless, refresh token rotation |
| Docs | Swagger (drf-spectacular) | Auto-generated, always up to date |
| Deployment | Render + Docker | Container-based, easy CI/CD |

---

## Project Structure

```
devboard/
├── docker-compose.yml
├── .env
├── django_app/
│   ├── Dockerfile
│   ├── start.sh
│   ├── requirements.txt
│   ├── manage.py
│   ├── celery_worker.py
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   └── apps/
│       ├── accounts/
│       ├── projects/
│       └── issues/
└── fastapi_app/
    ├── Dockerfile
    ├── requirements.txt
    └── main.py
```

---

## Running locally

**Prerequisites:** Docker and Docker Compose installed

```bash
git clone https://github.com/kushal-pandey/devboard.git
cd devboard

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up --build
```

That's it. Docker starts PostgreSQL, Redis, Django, Celery and FastAPI together.

| Service | URL |
|---|---|
| Django API | http://localhost:8000/api/ |
| Swagger Docs | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |
| FastAPI | http://localhost:8001/ |
| FastAPI Docs | http://localhost:8001/docs/ |

To create an admin user:
```bash
docker compose exec django python manage.py createsuperuser
```

---

## API Overview

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Create account |
| POST | `/api/auth/login/` | Login, returns JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/PUT | `/api/auth/profile/` | View or update profile |

### Projects
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/projects/` | List or create projects |
| GET/PUT/DELETE | `/api/projects/{id}/` | Manage a project |
| GET | `/api/projects/{id}/members/` | List members |
| POST | `/api/projects/{id}/add_member/` | Add a member |
| GET | `/api/projects/{id}/stats/` | Project stats (cached) |

### Issues
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/issues/` | List or create issues |
| GET/PUT/DELETE | `/api/issues/{id}/` | Manage an issue |
| GET/POST | `/api/issues/{id}/comments/` | Comments on an issue |

### Real-time (FastAPI)
| Type | Endpoint | Description |
|---|---|---|
| WebSocket | `/ws/project/{project_id}` | Live project room |
| GET | `/analytics/project/{id}/activity` | Recent events |
| GET | `/analytics/online/{project_id}` | Online user count |

Full interactive docs available at `/api/docs/` (Django) and `/docs/` (FastAPI).

---

## Live Demo

| Service | URL |
|---|---|
| Django API | https://devboard-9mjs.onrender.com/api/docs/ |
| FastAPI | https://devboard-fastapi.onrender.com/docs/ |

> Note: Hosted on Render free tier — first request may take 30–50 seconds if the service has spun down due to inactivity.

---

## Environment Variables

```env
SECRET_KEY=your-django-secret-key
DEBUG=0
DB_NAME=devboard
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-neon-host
DB_PORT=5432
REDIS_URL=redis://your-redis-url
DJANGO_API_URL=https://your-django-service.onrender.com
```

---

## What I learned building this

- How to structure a Django project with multiple apps cleanly
- When to use `select_related` vs `prefetch_related` to avoid N+1 queries
- How Celery and Redis work together as a task queue
- Why stateless JWT auth is preferred over session-based auth in APIs
- How WebSocket connection management works in FastAPI
- How to wire multiple Docker containers together with shared services
- How environment-specific configuration works in production deployments
