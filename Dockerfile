# ---- Builder stage ----
FROM python:3.11 AS builder
WORKDIR /app

# Copy only requirements first — pip install is cached if requirements.txt unchanged
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Final stage ----
FROM python:3.11-slim AS final
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app source
COPY app/ ./app/

# Create non-root user
RUN adduser --disabled-password --gecos "" --uid 1001 appuser
USER appuser

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]