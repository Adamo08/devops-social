# 🐳 DevOps Social - Docker Workshop Project

A Twitter-like social media application built with Docker to demonstrate containerization and multi-service orchestration.

## 🎯 What You'll Learn

- Building custom Docker images with Dockerfiles
- Multi-container orchestration with Docker Compose
- Database persistence with volumes
- Container networking and communication
- Health checks and service dependencies

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│   FastAPI   │────▶│ PostgreSQL  │
│  Frontend   │     │   Backend   │     │  Database   │
│  (Port 3000)│     │  (Port 8000)│     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## ❌ The Problem: Running Services Manually

Before we dive into the easy way, let's understand **why** Docker Compose exists. Imagine you need to run this application without Docker Compose. Here's what you'd have to do:

### Step 1: Start PostgreSQL
```bash
docker run -d \
  --name devops-social-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=devops_social \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine
```

### Step 2: Build and Start Backend
```bash
# First, build the backend image
docker build -t devops-social-backend ./backend

# Then run it with ALL the environment variables and network links
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

### Step 3: Build and Start Frontend
```bash
# Build the frontend image
docker build -t devops-social-frontend ./frontend

# Run it
docker run -d \
  --name devops-social-frontend \
  -p 3000:80 \
  devops-social-frontend
```

### Step 4: Start Database Admin Tool
```bash
docker run -d \
  --name devops-social-adminer \
  -p 8080:8080 \
  --link devops-social-db:db \
  adminer
```

### 😰 Problems with This Approach:

1. **Order Matters**: You must start database before backend, or backend will crash
2. **Manual Networking**: You need to figure out container IPs or use legacy `--link`
3. **Complex Commands**: Each service requires multiple flags and environment variables
4. **No Orchestration**: If database restarts, backend doesn't reconnect automatically
5. **Hard to Maintain**: Updating configuration means updating 5+ commands
6. **Error-Prone**: Easy to forget an environment variable or port mapping
7. **Difficult to Share**: How do you share these 5 commands with your team?
8. **No Dependency Management**: Services don't wait for health checks
9. **Manual Cleanup**: You need to stop and remove 5 containers individually
10. **Volume Management**: Manual tracking of volume names and cleanup

**Starting the app manually:**
```bash
# You'd need a script like this:
./start-database.sh
sleep 5  # Wait for database...
./start-backend.sh
sleep 3  # Wait for backend...
./start-frontend.sh
./start-adminer.sh
```

**Stopping the app manually:**
```bash
docker stop devops-social-frontend devops-social-backend \
  devops-social-db devops-social-adminer
docker rm devops-social-frontend devops-social-backend \
  devops-social-db devops-social-adminer
docker volume rm postgres_data  # If you want to clean up
```

---

## ✅ The Solution: Docker Compose

Docker Compose solves all these problems with a single configuration file. Instead of 4 complex commands, you get:

```yaml
# docker-compose.yml - One file to rule them all!
services:
  frontend: ...
  backend: ...
  db: ...
  adminer: ...
```

**Starting the app with Compose:**
```bash
docker compose up
```

**Stopping the app with Compose:**
```bash
docker compose down
```

That's it! Docker Compose handles:
- ✅ Service orchestration and startup order
- ✅ Automatic networking between containers
- ✅ Environment variable management
- ✅ Health checks and dependencies
- ✅ Volume management
- ✅ One-command start/stop/rebuild
- ✅ Easy to read, maintain, and share

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed (or Docker Engine + Docker Compose)
- No other services running on ports 3000, 8000, 8080

### Running the Application

1. **Clone or navigate to the project directory:**
   ```bash
   cd devops-social
   ```

2. **Start all services (with Docker Compose!):**
   ```bash
   docker compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Database Admin (Adminer): http://localhost:8080
   - API Documentation: http://localhost:8000/docs

### Stopping the Application

```bash
docker compose down
```

To remove all data (including database volumes):
```bash
docker compose down -v
```

## 📦 Services

### Frontend (Nginx)
- **Port:** 3000
- **Technology:** HTML/CSS/JavaScript served by Nginx
- **Features:** Beautiful UI with real-time updates every 5 seconds

### Backend (FastAPI)
- **Port:** 8000
- **Technology:** Python with FastAPI framework
- **Features:**
  - RESTful API endpoints
  - PostgreSQL database integration
  - Automatic database schema creation

### Database (PostgreSQL)
- **Technology:** PostgreSQL 15 (Alpine)
- **Features:**
  - Persistent data storage with volumes
  - Health checks for service readiness
  - Stores all posts with timestamps

### Admin (Adminer)
- **Port:** 8080
- **Features:**
  - Web-based database management
  - Query posts directly
  - Inspect database schema

## 📝 API Endpoints

### GET /
Returns API status message

### GET /posts
Returns all posts (up to 50 most recent)

### POST /posts
Create a new post
```json
{
  "username": "string",
  "content": "string"
}
```

### GET /stats
Returns application statistics
- Total posts count
- Docker magic indicator

## 🧪 Testing the Application

1. **Post a message:**
   - Open http://localhost:3000
   - Enter your name and a message
   - Click "Post It!"

2. **Explore the database:**
   - Open http://localhost:8080
   - Server: `db`
   - Username: `postgres`
   - Password: `postgres`
   - Database: `devops_social`

3. **View logs:**
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

## 🔧 Useful Docker Commands

```bash
# View running containers
docker compose ps

# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs backend -f

# Execute command in running container
docker compose exec backend bash

# Rebuild specific service
docker compose up --build backend

# View resource usage
docker stats
```

## ✨ Features

### Users Can:
- ✍️ Post messages with username
- 📖 Read all posts in chronological order
- 🕐 See timestamps for each post
- 📊 View application statistics

### Technical Highlights:
- RESTful API design
- Real-time UI updates (5-second refresh)
- Database persistence across restarts
- Beautiful gradient UI
- Health checks for reliability
- Docker networking for service communication

## 🏆 Challenges

Want to level up? Try these challenges:

### Challenge 1: Enhance the UI ⭐
- Add user avatars
- Add likes/reactions to posts
- Add delete functionality
- Implement dark mode

### Challenge 2: Add Authentication ⭐⭐
- Add user registration and login
- Implement JWT tokens
- Protect POST endpoints
- Add user profiles

### Challenge 3: Add More Features ⭐⭐⭐
- Add comments to posts
- Add image uploads
- Add hashtag search
- Add user following system

### Challenge 4: Production Ready ⭐⭐⭐⭐
- Add Nginx reverse proxy
- Add HTTPS with Let's Encrypt
- Add environment-based configs
- Add monitoring (Prometheus + Grafana)
- Add logging (ELK stack)

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000
# Kill the process or change port in docker-compose.yml
```

### Database Connection Failed
```bash
# Check if database is healthy
docker compose ps
# Wait for health check to pass
# View database logs
docker compose logs db
```

### Frontend Can't Reach Backend
- Check if backend is running: http://localhost:8000
- Verify CORS settings in backend/main.py
- Check browser console for errors

### Changes Not Reflecting
```bash
# Rebuild containers
docker compose up --build
# Or rebuild specific service
docker compose up --build frontend
```

## 📚 Learn More

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🎓 Workshop Context

This project is part of the Docker Workshop organized by the Computer Science Club. The workshop covers:
- Container vs VM concepts
- Docker fundamentals
- Building custom images
- Multi-container applications
- Real-world deployment patterns

## 📄 Project Structure

```
devops-social/
├── README.md
├── docker-compose.yml
├── .dockerignore
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── Dockerfile
    └── index.html
```

## 🤝 Contributing

Found a bug or have an idea? Feel free to:
- Open an issue
- Submit a pull request
- Share your enhancements with the community

## 📝 License

MIT - Learn, build, and share!

---

**Built with ❤️ and 🐳 for the Docker Workshop**

**Happy Dockering!** 🚀
