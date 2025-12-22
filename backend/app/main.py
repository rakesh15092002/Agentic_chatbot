from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- 1. IMPORT THIS
from app.routes.chat_routes import router as chat_router
from app.routes.thread_routes import router as thread_router
from app.db.sqlite_conn import init_db

app = FastAPI(title="LangGraph Chatbot with Threads")

# 2. ADD MIDDLEWARE HERE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allow your Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# Your routers...
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(thread_router, prefix="/thread", tags=["Thread"])

@app.get("/")
def root():
    return {"message": "Chatbot backend with threads running!"}