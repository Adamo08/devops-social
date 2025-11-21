from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
from datetime import datetime

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "devops_social"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

class Post(BaseModel):
    username: str
    content: str

@app.on_event("startup")
def startup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100),
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.get("/")
def read_root():
    return {"message": "🐳 DevOps Social API is live!"}

@app.get("/posts")
def get_posts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, content, created_at FROM posts ORDER BY created_at DESC LIMIT 50")
    posts = []
    for row in cur.fetchall():
        posts.append({
            "id": row[0],
            "username": row[1],
            "content": row[2],
            "created_at": str(row[3])
        })
    cur.close()
    conn.close()

    return {"posts": posts}

@app.post("/posts")
def create_post(post: Post):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (username, content) VALUES (%s, %s) RETURNING id",
        (post.username, post.content)
    )
    post_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {"id": post_id, "message": "Post created!"}

@app.get("/stats")
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM posts")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    return {
        "total_posts": count,
        "docker_magic": "🐳✨"
    }
