FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY alembic.ini ./
RUN useradd --create-home app && mkdir -p /app/backend/media && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["python", "-m", "backend.entrypoint"]
