#!/bin/bash

echo "Starting deployment of Zomato Agent..."

# Ensure we have the .env file
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating a default one."
    cat <<EOF > .env
MODEL_TYPE=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://host.docker.internal:11434
EOF
fi

# Stop any running containers
echo "Stopping existing containers..."
docker-compose down

# Build and start the services in detached mode
echo "Building and starting Docker containers..."
docker-compose up --build -d

echo "Deployment complete!"
echo "Frontend is available at: http://localhost:8501"
echo "Backend is available at: http://localhost:8000"
