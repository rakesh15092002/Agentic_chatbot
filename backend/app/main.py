from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat_routes import router as chat_router
from app.routes.thread_routes import router as thread_router
from app.db.sqlite_conn import init_db
from app.routes import document_routes
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LangGraph Chatbot with Threads")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database on Startup
init_db()

# Include Routers
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(thread_router, prefix="/thread", tags=["Thread"])
app.include_router(document_routes.router, prefix="/documents", tags=["Documents"])

@app.get("/")
def root():
    return {"message": "Chatbot backend is running!"}