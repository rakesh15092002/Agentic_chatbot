# Agentic Chatbot 🤖

An AI-powered chatbot application built with a Python backend and a Next.js (TypeScript) frontend. This repository contains the source code for both the client-side interface and the server-side logic.

## 🚀 Project Structure

This is a Monorepo structure:

- **`/backend`**: Python server (handling AI logic, database, and API).
- **`/frontend`**: Next.js & TypeScript application (user interface).

## 🛠️ Tech Stack

- **Frontend:** Next.js 14+, TypeScript, Tailwind CSS (assumed), Node.js
- **Backend:** Python, SQLite (`chatbot.db`)
- **AI/LLM:** (Add specific libraries here, e.g., LangChain, OpenAI, etc.)

---

## 🏁 Getting Started

Follow these instructions to set up the project locally on your machine.

### Prerequisites
Make sure you have the following installed:
- [Node.js](https://nodejs.org/) (Latest LTS version)
- [Python](https://www.python.org/) (3.10 or higher)
- [Git](https://git-scm.com/)

---

### 1️⃣ Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create and activate a virtual environment:
    * **Windows:**
        ```bash
        python -m venv myenv
        .\myenv\Scripts\activate
        ```
    * **Mac/Linux:**
        ```bash
        python3 -m venv myenv
        source myenv/bin/activate
        ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up Environment Variables:
    * Create a `.env` file in the `backend` folder.
    * Add your API keys (e.g., `OPENAI_API_KEY=your_key_here`).

5.  Run the Backend Server:
    ```bash
    # Command depends on your framework (Example for Flask/FastAPI)
    python app.py
    # OR if using uvicorn
    uvicorn app:app --reload
    ```

---

### 2️⃣ Frontend Setup

1.  Open a new terminal and navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install Node dependencies:
    ```bash
    npm install
    ```

3.  Set up Environment Variables:
    * Create a `.env.local` file in the `frontend` folder.
    * Add necessary public vars (e.g., `NEXT_PUBLIC_API_URL=http://localhost:5000`).

4.  Run the Development Server:
    ```bash
    npm run dev
    ```

5.  Open your browser and visit: `http://localhost:3000`

---

## 🤝 Contributing

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License.
