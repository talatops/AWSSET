#!/bin/bash
set -e

echo "🚀 Starting AWSSET Backend..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
  if python3 -c "
import sys
import psycopg2
import os
db_url = os.getenv('DATABASE_URL', 'postgresql://awschatbot:secure_password@db:5432/awschatbot_db')
try:
    conn = psycopg2.connect(db_url, connect_timeout=2)
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>&1 > /dev/null; then
    echo "✅ PostgreSQL is ready!"
    break
  fi
  retry_count=$((retry_count + 1))
  if [ $retry_count -ge $max_retries ]; then
    echo "❌ PostgreSQL connection failed after $max_retries attempts"
    echo "Attempting to continue anyway..."
    break
  fi
  echo "PostgreSQL is unavailable - sleeping ($retry_count/$max_retries)"
  sleep 1
done

# Wait for Redis to be ready (optional)
echo "⏳ Waiting for Redis to be ready..."
max_retries=10
retry_count=0

while [ $retry_count -lt $max_retries ]; do
  if python3 -c "
import sys
import redis
import os
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
try:
    r = redis.from_url(redis_url, socket_connect_timeout=1, decode_responses=True)
    r.ping()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>&1 > /dev/null; then
    echo "✅ Redis is ready!"
    break
  fi
  retry_count=$((retry_count + 1))
  if [ $retry_count -ge $max_retries ]; then
    echo "⚠️ Redis unavailable - continuing without Redis (will use fallbacks)"
    break
  fi
  sleep 1
done

# Run Alembic migrations
echo "📦 Running database migrations..."
cd /app
alembic upgrade head || {
    echo "⚠️ Migration failed, but continuing..."
}
echo "✅ Database migrations completed!"

# Start the application
echo "🚀 Starting FastAPI application..."
exec "$@"
