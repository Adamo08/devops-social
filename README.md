# Docker Workshop - Part 2: Multi-Service Application with Docker Compose

A hands-on workshop demonstrating multi-container orchestration using a Twitter-like social media application.

## Table of Contents
- [The Problem](#the-problem)
- [Getting Started](#getting-started)
- [Workshop Structure](#workshop-structure)
- [Project Architecture](#project-architecture)
- [Phase 1: Manual Container Management](#phase-1-manual-container-management)
- [Phase 2: Introducing Docker Compose](#phase-2-introducing-docker-compose)
- [Essential Docker Compose Commands](#essential-docker-compose-commands)
- [Testing Your Application](#testing-your-application)
- [What You've Learned](#what-youve-learned)

---

## The Problem

In Part 1, you learned how to containerize a single application. But real-world applications are rarely that simple. Most production systems consist of **multiple services** that need to work together:

- **Frontend** (web server serving HTML/CSS/JS)
- **Backend** (API server with business logic)
- **Database** (persistent data storage)
- **Caching layer** (Redis, Memcached)
- **Message queue** (RabbitMQ, Kafka)

### The Challenge: Managing Multiple Containers

Imagine you have 3 services (like our app: Frontend, Backend, Database). Without Docker Compose, you would need to:

1. **Start containers in the correct order** (database first, then backend, then frontend)
2. **Manually configure networking** between containers
3. **Track multiple environment variables** for each service
4. **Remember complex docker run commands** with many flags
5. **Stop and remove** each container individually
6. **Rebuild and restart** everything when code changes

**For a team of developers, this becomes a nightmare:**
- Dev A forgets to start the database first → backend crashes
- Dev B uses wrong environment variables → can't connect to database
- Dev C rebuilds only backend, forgets frontend → stale UI
- Dev D can't remember the exact `docker run` command → wastes 30 minutes debugging

**This doesn't scale!**

---

## Getting Started

### Prerequisites:
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Git installed
- Completed Part 1 of the workshop (recommended)
- Text editor of your choice

**Note for Windows users:** Use **Git Bash** to run the commands in this workshop, not CMD or PowerShell. Git Bash provides a Unix-like terminal that supports the same commands as Linux/macOS.

### Clone and Navigate:
```bash
# Clone the repository
git clone https://github.com/Adamo08/devops-social.git

# Navigate to the project directory
cd devops-social
```

---

## Workshop Structure

### Branches:
- `main` - Starting point (application code only, no Docker files)
- `solution` - Complete solution with Dockerfiles and docker-compose.yml

### Switching Branches:
```bash
# View all branches
git branch -a

# Switch to solution branch (if you get stuck)
git checkout solution

# Go back to main to continue the workshop
git checkout main
```

---

## Project Architecture

This is a **3-tier web application** (Twitter-like social media platform):

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP request to localhost:3000
       ▼
┌─────────────────────────┐
│  Frontend (Nginx)       │
│  Port: 3000             │
│  - HTML/CSS/JavaScript  │
│  - Served by Nginx      │
└──────┬──────────────────┘
       │ Fetch API requests via CORS
       │ to localhost:8000
       ▼
┌──────────────────────────┐
│  Backend (FastAPI)       │
│  Port: 8000              │
│  - Python REST API       │
│  - Business logic        │
│  - Database operations   │
└──────┬───────────────────┘
       │ psycopg2 connection
       │ to db:5432
       ▼
┌──────────────────────────┐
│  Database (PostgreSQL)   │
│  Port: 5432              │
│  - Stores posts          │
│  - Persistent storage    │
└──────────────────────────┘
```

### Services Overview:

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| **Frontend** | Nginx (Alpine) | 3000 | Serves static HTML/CSS/JS UI |
| **Backend** | Python 3.11 + FastAPI | 8000 | RESTful API, business logic |
| **Database** | PostgreSQL 15 (Alpine) | 5432 | Persistent data storage |

---

## Phase 1: Manual Container Management

In this phase, you'll experience the **pain** of managing multiple containers manually. This will help you appreciate Docker Compose later!

### Step 1.1: Create Dockerfiles

You need to create a Dockerfile for each service that needs to be built.

#### Task 1: Create Backend Dockerfile

Create `backend/Dockerfile`:

**Requirements:**
- Base image: `python:3.11-slim`
- Working directory: `/app`
- Copy `requirements.txt` and install dependencies
- Copy all backend code
- Expose port `8000`
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000`

**Hint:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Task 2: Create Frontend Dockerfile

Create `frontend/Dockerfile`:

**Requirements:**
- Base image: `nginx:alpine`
- Copy `index.html` to `/usr/share/nginx/html/`
- Expose port `80`
- Command: `nginx -g "daemon off;"`

**Hint:**
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

### Step 1.2: Build Your Images

Build Docker images for each service:

```bash
# Build backend image
docker build -t devops-social-backend ./backend

# Build frontend image
docker build -t devops-social-frontend ./frontend
```

Verify images were created:
```bash
docker images | grep devops-social
```

---

### Step 1.3: Run Containers Manually (The Hard Way)

Now let's start all containers manually. **Pay attention to the order and complexity!**

#### Why Order Matters - A Quick Experiment

**What happens if you start the backend first?** Let's try it:

```bash
# Try to start backend WITHOUT the database running
docker run -d \
  --name devops-social-backend \
  -p 8000:8000 \
  -e DB_HOST=devops-social-db \
  -e DB_NAME=devops_social \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  devops-social-backend
```

**Check the logs:**
```bash
docker logs devops-social-backend
```

**Result:** ❌ Backend crashes! It can't connect to the database because it doesn't exist yet.

You'll see errors like:
```
psycopg2.OperationalError: could not translate host name "devops-social-db" to address
```

**Clean up the failed backend:**
```bash
docker stop devops-social-backend
docker rm devops-social-backend
```

**This demonstrates a critical problem: Service dependencies must be managed manually!**

Now let's do it the correct way:

---

#### Step 1.3.1: Start the Database First

**Why first?** Because the backend depends on it!

```bash
docker run -d \
  --name devops-social-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=devops_social \
  -p 5432:5432 \
  postgres:15-alpine
```

**Explanation of flags:**
- `-d` - Run in detached mode (background)
- `--name` - Give container a custom name for reference
- `-e` - Set environment variables (database credentials)
- `-p` - Publish port (host:container)

**Wait for database to be ready** (give it ~5-10 seconds):
```bash
# Check if database is ready
docker logs devops-social-db
```

---

#### Step 1.3.2: Start the Backend Second

**Why second?** It needs to connect to the database!

```bash
docker run -d \
  --name devops-social-backend \
  -p 8000:8000 \
  -e DB_HOST=devops-social-db \
  -e DB_NAME=devops_social \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  --link devops-social-db:db \
  devops-social-backend
```

**Explanation of additional flags:**
- `--link` - Legacy way to connect containers (deprecated but simple for demonstration)

**Wait and verify:**
```bash
# Check backend logs for successful database connection
docker logs devops-social-backend
```

---

#### Step 1.3.3: Start the Frontend Last

```bash
docker run -d \
  --name devops-social-frontend \
  -p 3000:80 \
  devops-social-frontend
```

---

### Step 1.4: Test the Manual Setup

Open your browser:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Try posting a message!

---

### Step 1.5: The Problems You Just Experienced

Let's reflect on what you just did:

**Problems:**
1. ❌ **Critical Startup Order:**
   - If you start backend before database → backend crashes
   - If you start frontend before backend → API calls fail
   - You MUST remember: database → backend → frontend (always!)

2. ❌ **No Automatic Dependency Management:**
   - Docker doesn't know backend depends on database
   - You must manually ensure the database is ready before starting backend
   - One wrong order = everything fails

3. ❌ **Long Commands:** Each `docker run` has 5+ flags to remember

4. ❌ **Environment Variables:** Easy to mistype or forget one

5. ❌ **Container Linking:** Using deprecated `--link` flag to connect containers

6. ❌ **Hard to Share:** How do you tell your teammate these exact steps?

7. ❌ **Difficult Updates:** Change one thing → restart everything manually

8. ❌ **Manual Cleanup:** Need to stop and remove each container individually

**Stop all containers manually:**
```bash
docker stop devops-social-frontend devops-social-backend devops-social-db
docker rm devops-social-frontend devops-social-backend devops-social-db
```

**Frustrating, right?** This is exactly why Docker Compose was created!

---

## Phase 2: Introducing Docker Compose

Docker Compose is a tool that lets you define and run multi-container applications using a single YAML configuration file.

### The Magic of Docker Compose

Instead of remembering 3+ complex `docker run` commands, you write **one configuration file** and use **two simple commands**:

```bash
docker compose up      # Start everything
docker compose down    # Stop everything
```

---

### Step 2.1: Create docker-compose.yml

Create a file named `docker-compose.yml` in the project root.

**Your Task:** Define all three services in one file.

#### Minimal Docker Compose Structure (No Volumes/Networks)

```yaml
services:
  # Database service
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: devops_social
    ports:
      - "5432:5432"

  # Backend service
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DB_HOST: db
      DB_NAME: devops_social
      DB_USER: postgres
      DB_PASSWORD: postgres
    depends_on:
      - db

  # Frontend service
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

**Key Concepts:**

| Field | Description |
|-------|-------------|
| `services:` | Defines all containers in your application |
| `image:` | Pre-built image to use (for db) |
| `build:` | Path to Dockerfile to build (for backend/frontend) |
| `ports:` | Port mapping (host:container) |
| `environment:` | Environment variables |
| `depends_on:` | Service startup order |

**Magic Happening Behind the Scenes:**
- ✅ Docker Compose creates a **default network** automatically
- ✅ Services can reach each other using **service names** (e.g., `db`, `backend`)
- ✅ Services start in **dependency order** (db → backend → frontend)
- ✅ All configuration in **one readable file**

---

### Step 2.2: Start Everything with One Command

```bash
# Start all services (builds images if needed)
docker compose up --build

# Or run in detached mode (background)
docker compose up -d --build
```

**What just happened?**
1. Docker Compose read your `docker-compose.yml`
2. Created a default network (`devops-social_default`)
3. Built the backend and frontend images
4. Started `db` first (no dependencies)
5. Started `backend` after `db` (depends_on)
6. Started `frontend` after `backend` (depends_on)
7. All services can communicate using service names

**⚠️ Potential Issue: Backend May Crash on First Start**

You might see an error like this:
```
backend-1 | psycopg2.OperationalError: connection to server at "db" failed: Connection refused
backend-1 exited with code 3
```

**Why?** The basic `depends_on` only waits for the **container to start**, not for PostgreSQL to be **ready to accept connections**. The database needs a few seconds to initialize.

**Quick Fix:** Simply run the command again:
```bash
docker compose up
```

The database is now ready, and backend will start successfully!

**Proper Solution:** This issue is solved with **health checks** (see Challenge 3 below or check the `solution` branch). Health checks make `depends_on` smarter by waiting for the service to be actually ready.

**Access your application:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

### Step 2.3: Stop Everything with One Command

```bash
# Stop and remove all containers
docker compose down

# Stop and remove containers + volumes (delete all data)
docker compose down -v
```

**Compare:**

**Manual Way (The Pain):**
```bash
docker stop devops-social-frontend devops-social-backend devops-social-db
docker rm devops-social-frontend devops-social-backend devops-social-db
docker network rm devops-social-network
```

**Docker Compose Way (The Joy):**
```bash
docker compose down
```

---

### Step 2.4: Understanding Service Communication

With Docker Compose, services use **service names** as hostnames:

**In `backend/main.py`:**
```python
# Backend connects to database using service name "db"
DB_HOST = os.getenv("DB_HOST", "db")  # "db" is the service name!
```

**In `docker-compose.yml`:**
```yaml
backend:
  environment:
    DB_HOST: db  # This resolves to the "db" service's IP automatically
```

**Docker Compose handles DNS resolution** so you never need to know container IPs!

---

### Step 2.5: How Docker Run Flags Map to Docker Compose

Here's how the complex `docker run` commands translate to clean YAML:

| docker run flag | docker-compose.yml field |
|----------------|-------------------------|
| `--name myapp` | Service name (e.g., `backend:`) |
| `-p 8000:8000` | `ports: - "8000:8000"` |
| `-e KEY=value` | `environment: KEY: value` |
| `--network mynet` | Automatic (default network) |
| `-v vol:/data` | `volumes: - vol:/data` |
| `-d` | `docker compose up -d` |
| `--rm` | `docker compose down` removes containers |

---

## Essential Docker Compose Commands

### Starting and Stopping:
```bash
# Start all services (foreground, see logs)
docker compose up

# Start all services in background
docker compose up -d

# Start and rebuild images
docker compose up --build

# Start specific service
docker compose up backend

# Stop all services
docker compose down

# Stop and remove volumes (delete data)
docker compose down -v
```

### Monitoring:
```bash
# View running services
docker compose ps

# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs backend

# Follow logs in real-time
docker compose logs -f

# View last 100 lines
docker compose logs --tail=100
```

### Rebuilding and Restarting:
```bash
# Rebuild specific service
docker compose build backend

# Rebuild all services
docker compose build

# Restart specific service
docker compose restart backend

# Restart all services
docker compose restart
```

### Executing Commands in Containers:
```bash
# Open shell in backend container
docker compose exec backend bash

# Run a one-off command
docker compose exec backend python -c "print('Hello')"

# Access database CLI
docker compose exec db psql -U postgres -d devops_social
```

### Inspecting and Debugging:
```bash
# View service configuration
docker compose config

# Validate docker-compose.yml
docker compose config --quiet

# View resource usage
docker stats

# Inspect network
docker network ls
docker network inspect devops-social_default
```

---

## Testing Your Application

### 1. Post a Message

1. Open http://localhost:3000
2. Enter your username
3. Type a message
4. Click "Post It!"
5. Watch it appear in the feed (refreshes every 5 seconds)

### 2. Check the Backend API

Visit http://localhost:8000/docs to see interactive API documentation (FastAPI auto-generates this!)

**Try these endpoints:**
- `GET /` - Health check
- `GET /posts` - Get all posts
- `POST /posts` - Create a post
- `GET /stats` - View statistics

### 3. Inspect the Database

**Option 1: Using Adminer (Optional)**

Add this to your `docker-compose.yml`:
```yaml
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - db
```

Then access http://localhost:8080:
- System: PostgreSQL
- Server: `db`
- Username: `postgres`
- Password: `postgres`
- Database: `devops_social`

**Option 2: Using psql CLI**
```bash
# Access PostgreSQL shell
docker compose exec db psql -U postgres -d devops_social

# Query posts
SELECT * FROM posts;

# Exit
\q
```

### 4. View Logs

```bash
# View all logs
docker compose logs

# View backend logs
docker compose logs backend -f

# View database logs
docker compose logs db --tail=50
```

---

## What You've Learned

### Part 1 Recap:
1. **Single Container:** Dockerfile → Build → Run → Push to Docker Hub
2. **Image Sharing:** Why sharing images is better than Dockerfiles for teams

### Part 2 New Concepts:
1. **Multi-Container Apps:** Real applications have multiple services
2. **Manual Container Management:** The pain of `docker run` with many flags
3. **Service Dependencies:** Order matters (db → backend → frontend)
4. **Container Networking:** How services communicate using service names
5. **Docker Compose Benefits:**
   - One configuration file (`docker-compose.yml`)
   - One command to start (`docker compose up`)
   - One command to stop (`docker compose down`)
   - Automatic networking between services
   - Dependency management with `depends_on`
6. **docker run → docker-compose mapping:** How flags translate to YAML

### Key Insights:

**Before Docker Compose:**
- 3+ complex `docker run` commands
- Manual network creation
- Manual startup order
- Easy to make mistakes
- Hard to share with team

**After Docker Compose:**
- 1 readable YAML file
- Automatic networking
- Automatic startup order
- Consistent across team
- Easy to version control

---

## Next Steps

Want to go deeper? Try these challenges:

### Challenge 1: Add Data Persistence ⭐
Currently, if you run `docker compose down`, all database data is lost. Add a **volume** to persist data:

```yaml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Challenge 2: Add Environment File ⭐⭐
Instead of hardcoding environment variables, use a `.env` file:

```yaml
services:
  backend:
    env_file:
      - .env
```

Create `.env`:
```
DB_HOST=db
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=devops_social
```

### Challenge 3: Add Health Checks ⭐⭐⭐
Make `depends_on` smarter by adding health checks:

```yaml
services:
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    depends_on:
      db:
        condition: service_healthy
```

### Challenge 4: Custom Networks ⭐⭐⭐
Learn how to create custom networks for better isolation and control:

```yaml
services:
  backend:
    networks:
      - app-network
      - db-network

  frontend:
    networks:
      - app-network

  db:
    networks:
      - db-network

networks:
  app-network:
    driver: bridge
  db-network:
    driver: bridge
```

**Why use custom networks?**
- **Isolation:** Frontend can't directly access database
- **Security:** Only backend can talk to database
- **Organization:** Group related services together

**Practical Example for Our Application:**

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: devops_social
    networks:
      - backend-network  # Only accessible by backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DB_HOST: db
      DB_NAME: devops_social
      DB_USER: postgres
      DB_PASSWORD: postgres
    depends_on:
      - db
    networks:
      - backend-network  # Can access database
      - frontend-network # Can be accessed by frontend

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - frontend-network  # Can access backend only

networks:
  frontend-network:
  backend-network:
```

**Benefits:**
- Frontend → Backend ✅ (via frontend-network)
- Backend → Database ✅ (via backend-network)
- Frontend → Database ❌ (isolated, more secure!)

### Challenge 5: Production Setup ⭐⭐⭐⭐
- Add Nginx reverse proxy
- Use separate `docker-compose.prod.yml`
- Add logging configuration
- Use Docker secrets for passwords

---

## Troubleshooting

### Port Already in Use
```bash
# Linux/macOS: Find what's using port 3000
sudo lsof -i :3000

# Windows (PowerShell): Find what's using port 3000
netstat -ano | findstr :3000

# Or simply change the port in docker-compose.yml
# Change "3000:80" to "3001:80" for frontend
```

### Service Won't Start
```bash
# Check logs
docker compose logs backend

# Check service status
docker compose ps

# Rebuild from scratch
docker compose down
docker compose up --build
```

### Database Connection Failed
```bash
# Check if db is running
docker compose ps db

# View database logs
docker compose logs db

# Restart database
docker compose restart db
```

### Changes Not Reflecting
```bash
# Rebuild services
docker compose up --build

# Or rebuild specific service
docker compose up --build backend
```

### Clean Slate
```bash
# Remove everything (containers, networks, volumes, images)
docker compose down -v --rmi all

# Start fresh
docker compose up --build
```

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Nginx Docker Image](https://hub.docker.com/_/nginx)

---

## What's in This Repository

**Application Code:**
- `backend/` - Python FastAPI server
  - `main.py` - API endpoints and database logic
  - `requirements.txt` - Python dependencies
- `frontend/` - Static web UI
  - `index.html` - Single-page application

**Workshop Files:**
- `README.md` - This comprehensive guide
- `DOCKER-CHEATSHEET.md` - Quick reference for Docker commands

---

**Built with ❤️ and 🐳 for the Docker Workshop**

Happy Dockerizing! 🚀
