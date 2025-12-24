# ==========================================
# STAGE 1: Build Next.js Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .

# Build Next.js
# This creates the .next folder
RUN npm run build

# ==========================================
# STAGE 2: Final Image (Python + Node)
# ==========================================
FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

WORKDIR /app

# 1. Install Supervisor (Process Manager)
RUN apt-get update && \
    apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/*

# 2. Setup Backend (FastAPI)
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# 3. Setup Frontend (Next.js)
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Install production dependencies only to save space
RUN npm install --omit=dev

# Copy the built artifacts from Stage 1
COPY --from=frontend-builder /app/frontend/.next ./.next
COPY --from=frontend-builder /app/frontend/public ./public
COPY frontend/next.config.mjs ./
# If you have other config files like tailwind.config.js, copy them too if needed, 
# but usually .next contains what is needed.

# 4. Configure Supervisor
# We run TWO programs: FastAPI (port 8000) and Next.js (port 3000)
WORKDIR /app
RUN echo "[supervisord]" > /etc/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisord.conf && \
    \
    # --- FastAPI Service ---
    echo "[program:fastapi]" >> /etc/supervisord.conf && \
    echo "directory=/app/backend" >> /etc/supervisord.conf && \
    # Using python -m uvicorn ensures we find the module
    echo "command=python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" >> /etc/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisord.conf && \
    \
    # --- Next.js Service ---
    echo "[program:nextjs]" >> /etc/supervisord.conf && \
    echo "directory=/app/frontend" >> /etc/supervisord.conf && \
    echo "command=npm start -- -p 3000" >> /etc/supervisord.conf && \
    echo "stdout_logfile=/dev/stdout" >> /etc/supervisord.conf && \
    echo "stdout_logfile_maxbytes=0" >> /etc/supervisord.conf && \
    echo "stderr_logfile=/dev/stderr" >> /etc/supervisord.conf && \
    echo "stderr_logfile_maxbytes=0" >> /etc/supervisord.conf

# Azure App Service usually routes traffic to port 80 or 8080 by default, 
# but we can configure it to look at 3000.
EXPOSE 3000 8000

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
