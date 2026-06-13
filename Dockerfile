# ---- Builder stage ----
FROM python:3.11 AS builder
WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first — pip install is cached if requirements.txt unchanged
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Final stage ----
FROM python:3.11-slim AS final
WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv

# Copy app source
COPY app/ ./app/

# Create non-root user
RUN adduser --disabled-password --gecos "" --uid 1001 appuser
USER appuser

# Make sure scripts in virtual env are usable
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]