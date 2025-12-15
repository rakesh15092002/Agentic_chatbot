from fastapi import FastAPI
from app.routes.chat_routes import router as chat_router
from app.routes.thread_routes import router as thread_router
from app.db.sqlite_conn import init_db

app = FastAPI(title="LangGraph Chatbot with Threads")

# Initialize DB (threads + messages tables)
init_db()

# Include routers
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(thread_router, prefix="/thread", tags=["Thread"])

@app.get("/")
def root():
    return {"message": "Chatbot backend with threads running!"}
