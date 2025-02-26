# Stage 1: Build stage
FROM python:3.12-slim AS build

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/usr/local -r requirements.txt

# Copy application code to the build stage
COPY main.py .

# Stage 2: Runtime stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=build /usr/local /usr/local
COPY --from=build /app/main.py .

# Set environment variables
ENV WS_HOST=0.0.0.0
ENV WS_PORT=6789

# Expose WebSocket port
EXPOSE 6789

# Command to run the WebSocket server
CMD ["python", "main.py"]