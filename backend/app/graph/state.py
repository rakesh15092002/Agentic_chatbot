from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# This class defines how your chatbot's state looks.
# Beginner-friendly: only a messages list.
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
