# 🤖 Agentic Chatbot with MCP Integration

An advanced AI chatbot powered by LangGraph, Groq (Llama 3.3), and Model Context Protocol (MCP) with GitHub integration. Features include real-time web search, document Q&A, mathematical calculations, and GitHub repository exploration.

![Chatbot Demo](https://via.placeholder.com/800x400?text=Add+Your+Screenshot+Here)

## ✨ Features

- **🧠 Advanced AI Reasoning**: Powered by Llama 3.3 70B via Groq API
- **🔧 Dynamic Tool Usage**: Automatically selects and executes appropriate tools
- **🐙 GitHub Integration**: Search repositories, read files, view commits via MCP
- **🌐 Web Search**: Real-time information retrieval using DuckDuckGo
- **📄 Document Q&A**: Upload and query PDF documents
- **🧮 Calculator**: Perform complex mathematical calculations
- **💬 Conversational Memory**: Context-aware multi-turn conversations
- **⚡ Streaming Responses**: Real-time token-by-token response generation

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  Next.js + React + TailwindCSS
│  (Client)   │
└──────┬──────┘
       │
       ↓ HTTP/SSE
┌──────────────┐
│   Backend    │  FastAPI + LangGraph
│  (Server)    │
└──────┬───────┘
       │
       ├─→ Groq API (Llama 3.3)
       ├─→ MCP Server (GitHub)
       ├─→ DuckDuckGo Search
       └─→ SQLite (Chat History)
```

## 🚀 Tech Stack

### Backend
- **Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **LLM**: Groq API (Llama 3.3 70B)
- **Tools**: LangChain, MCP (Model Context Protocol)
- **Database**: SQLite with WAL mode
- **Language**: Python 3.10+

### Frontend
- **Framework**: Next.js 14
- **UI Library**: React 18
- **Styling**: TailwindCSS
- **Icons**: React Icons
- **HTTP Client**: Fetch API with SSE

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm or yarn
- Groq API key ([Get it here](https://console.groq.com))
- GitHub Personal Access Token (for MCP integration)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/agentic-chatbot.git
cd agentic-chatbot
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv myenv

# Activate virtual environment
# Windows:
myenv\Scripts\activate
# Linux/Mac:
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

**Edit `.env` and add your API keys:**

```env
GROQ_API_KEY=your_groq_api_key_here
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.example .env.local
```

**Edit `.env.local`:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎮 Running the Application

### Start Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:3000`

## 📚 Usage

### Basic Chat

Simply type your message and press Enter. The bot will respond with helpful information.

```
User: What is the capital of France?
Bot: The capital of France is Paris.
```

### Using Calculator

```
User: Calculate 456 * 789
Bot: 456 * 789 = 359,784
```

### Web Search

```
User: Who is the current CEO of Apple?
Bot: The current CEO of Apple is Tim Cook.
```

### GitHub Integration

Enable the GitHub toggle and try:

```
User: Find popular Python web frameworks on GitHub
Bot: Here are some popular Python web frameworks...

User: Show me the README from django/django
Bot: [Displays README content]

User: List recent commits from facebook/react
Bot: [Shows commit history]
```

### Document Q&A

1. Click the upload button
2. Select a PDF file
3. Ask questions about the document

```
User: Summarize the uploaded document
Bot: [Provides summary based on PDF content]
```

## 🔧 Configuration

### Adjusting Token Limits

Edit `backend/app/graph/langgraph_setup.py`:

```python
trimmed_conversation = trim_messages(
    conversation_part,
    max_tokens=5000,  # Adjust this value
    strategy="last",
    ...
)
```

### Changing AI Model

Edit `backend/app/graph/langgraph_setup.py`:

```python
llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # or "llama-3.1-8b-instant"
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)
```

### Adding More Tools

Add your custom tools in `backend/app/utils/tools.py`:

```python
from langchain.tools import Tool

def my_custom_tool(input: str) -> str:
    # Your logic here
    return result

custom_tool = Tool(
    name="my_tool",
    func=my_custom_tool,
    description="Description of what the tool does"
)

tools = [calculator, duckduckgo_search, custom_tool]
```

## 📁 Project Structure

```
agentic-chatbot/
├── backend/
│   ├── app/
│   │   ├── graph/
│   │   │   └── langgraph_setup.py    # LangGraph configuration
│   │   ├── services/
│   │   │   ├── chat_service.py       # Chat logic
│   │   │   ├── mcp_manager.py        # GitHub MCP client
│   │   │   └── thread_service.py     # Chat history
│   │   ├── routes/
│   │   │   ├── chat_routes.py        # Chat endpoints
│   │   │   └── thread_routes.py      # Thread management
│   │   ├── utils/
│   │   │   └── tools.py              # Static tools
│   │   └── schemas/
│   │       └── chat_schema.py        # Pydantic models
│   ├── main.py                       # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── chat/
│   │   │   └── [id]/page.jsx        # Chat interface
│   │   └── page.jsx                 # Home page
│   ├── components/
│   │   ├── PromptBox.jsx            # Input component
│   │   └── Sidebar.jsx              # Chat history
│   ├── context/
│   │   └── AppContext.jsx           # Global state
│   └── package.json
└── README.md
```

## 🐛 Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError`
```bash
pip install -r requirements.txt --upgrade
```

**Issue**: `Could not import transformers`
```bash
pip install transformers
```

**Issue**: Rate limit errors from Groq
- Switch to `llama-3.1-8b-instant` model (10x cheaper)
- Or upgrade your Groq tier

### Frontend Issues

**Issue**: Cannot connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `main.py`

**Issue**: GitHub toggle not working
- Verify `GITHUB_PERSONAL_ACCESS_TOKEN` is set
- Check MCP server logs

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://www.langchain.com/) for the amazing AI orchestration framework
- [Groq](https://groq.com/) for lightning-fast LLM inference
- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- [Vercel](https://vercel.com/) for Next.js

## 📞 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter)

Project Link: [https://github.com/yourusername/agentic-chatbot](https://github.com/yourusername/agentic-chatbot)

---

⭐ If you found this project helpful, please give it a star!
