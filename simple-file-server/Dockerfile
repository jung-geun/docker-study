FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies for the FastAPI file server.
RUN pip install --no-cache-dir "fastapi[standard]" uvicorn python-multipart

COPY app.py ./

ENV PORT=3001
ENV UPLOAD_DIR=/var/uploads
ENV LOG_PATH=/var/log/app.log

RUN mkdir -p "$UPLOAD_DIR" && mkdir -p "$(dirname $LOG_PATH)"

EXPOSE 3001

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-3000}"]
