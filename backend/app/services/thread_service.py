from app.db.sqlite_conn import get_connection
import uuid
from langchain_core.messages import HumanMessage, AIMessage

# 1️⃣ Create a new thread
def create_thread(name: str = "New Chat"):
    thread_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO threads (id, name) VALUES (?, ?)",
        (thread_id, name)
    )
    conn.commit()
    conn.close()
    return thread_id

# 2️⃣ Save a message
def save_message(thread_id: str, role: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)",
        (thread_id, role, content)
    )
    conn.commit()
    conn.close()

# 3️⃣ Get all messages of a thread (LangChain objects)
def get_thread_messages(thread_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM messages WHERE thread_id=? ORDER BY created_at",
        (thread_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        if row["role"] == "user":
            messages.append(HumanMessage(content=row["content"]))
        else:
            messages.append(AIMessage(content=row["content"]))
    return messages

# 4️⃣ Get all messages of a thread for API (dicts for frontend)
def get_thread_messages_for_api(thread_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, created_at FROM messages WHERE thread_id=? ORDER BY created_at",
        (thread_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {"role": row["role"], "content": row["content"], "created_at": row["created_at"]}
        for row in rows
    ]

# 5️⃣ List all threads
def get_threads():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM threads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
