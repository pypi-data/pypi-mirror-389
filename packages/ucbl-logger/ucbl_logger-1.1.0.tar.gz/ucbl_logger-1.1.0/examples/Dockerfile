FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the logger package and example
COPY ../ucbl_logger ./ucbl_logger
COPY fastapi_nicegui_example.py .

# Expose port
EXPOSE 8080

# Set environment variables for container
ENV HOST=0.0.0.0
ENV PORT=8080

# Run the application
CMD ["python", "fastapi_nicegui_example.py"]