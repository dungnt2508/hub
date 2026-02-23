FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1


# Install system dependencies and timezone data
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set timezone to Vietnam
ENV TZ=Asia/Ho_Chi_Minh
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create app directory
WORKDIR /app

# Install Python dependencies for development
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code - prod mode
#COPY app/ /app/app/

# Copy scripts & migrations
#COPY scripts/ /app/scripts/
COPY alembic.ini /app/alembic.ini
COPY alembic/ /app/alembic/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8386

# Sử dụng startup.py để tự động config log level theo ENVIRONMENT
CMD ["python", "scripts/startup.py"]
