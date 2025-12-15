import sqlite3
from dotenv import load_dotenv
from os import getenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, Annotated
from app.graph.state import ChatState
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()

# --- SQLITE CHECKPOINTER ---
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Initialize Groq LLM
api_key = getenv("GROQ_API_KEY")  
model = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key)

# Chat node
def chat_node(state: ChatState):
    """
    LangGraph node that takes the current conversation state,
    invokes Groq model, appends AI response to messages, and returns updated state
    """
    messages = state['messages']  # previous messages included
    response = model.invoke(messages)
    messages.append(response)
    return {'messages': messages}

# Setup state graph
graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

# Compiled chatbot object
chatbot = graph.compile()
