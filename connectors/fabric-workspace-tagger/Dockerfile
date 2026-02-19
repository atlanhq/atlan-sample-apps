# Dockerfile for Microsoft Fabric Workspace Tagger app
# Based on Atlan Application SDK base image

FROM ghcr.io/atlanhq/application-sdk-base:2.3.1

WORKDIR /app

# Copy application code
COPY app/ ./app/
COPY main.py ./
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir .

# Expose server port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
