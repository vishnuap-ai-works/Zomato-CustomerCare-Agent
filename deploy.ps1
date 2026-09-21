Write-Host "Starting deployment of Zomato Agent..."

# Ensure we have the .env file
if (-not (Test-Path .env)) {
    Write-Host "Warning: .env file not found. Creating a default one." -ForegroundColor Yellow
    $envContent = @"
MODEL_TYPE=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://host.docker.internal:11434
"@
    Set-Content -Path .env -Value $envContent -Encoding UTF8
}

# Stop any running containers
Write-Host "Stopping existing containers..."
docker-compose down

# Build and start the services in detached mode
Write-Host "Building and starting Docker containers..."
docker-compose up --build -d

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Frontend is available at: http://localhost:8501"
Write-Host "Backend is available at: http://localhost:8000"
