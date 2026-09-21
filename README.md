# Zomato AI Customer Care Agent

An autonomous, multi-agent customer care system built with LangChain, FastAPI, and Streamlit. The agent operates within a distributed microservices architecture, interacting with dedicated REST APIs to manage user accounts, orders, automated complaints, and driver tracking.

## Features
- **Seamless Authentication (OTP)**
- **Session Management (5-minute inactivity timeouts)**
- **Driver Tracking & Communication (Mock SMS)**
- **Autonomous Complaint Handling & Wallet Refunds**
- **Wallet Balance Checking**
- **Subscription Renewals & Payment Links**
- **Live Status & Delay Reasons**
- **Address Modifications**
- **Proactive Assistance**

## Prerequisites
- Docker & Docker Compose
- OpenAI API Key (or local Ollama instance)

## Setup & Deployment

1. **Environment Variables:**
   The `deploy.sh` script automatically generates a default `.env` file if it doesn't exist. You can manually create or edit the `.env` file in the root directory:
   ```env
   MODEL_TYPE=openai
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4o-mini
   OLLAMA_MODEL=llama3
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

2. **Deploy the Microservices:**
   Execute the deployment script to build the Docker containers and start the network in detached mode:
   
   **For Linux / macOS:**
   ```bash
   ./deploy.sh
   ```

   **For Windows (PowerShell):**
   ```powershell
   .\deploy.ps1
   ```
   *Note: Ensure Docker daemon is running before executing.*
   
   Alternatively, you can deploy manually using `docker-compose`:
   ```bash
   docker-compose up --build -d
   ```

3. **Managing the Deployment:**
   - **View Logs**: To monitor the logs of all running services:
     ```bash
     docker-compose logs -f
     ```
   - **Stop Services**: To bring down the deployment:
     ```bash
     docker-compose down
     ```

4. **Access the Application:**
   - **Frontend (Chat UI)**: [http://localhost:8501](http://localhost:8501)
   - **Agent API (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Order Service API**: [http://localhost:8001/docs](http://localhost:8001/docs)
   - **User Service API**: [http://localhost:8002/docs](http://localhost:8002/docs)

## Mock Authentication & Seeded Users

To safely demonstrate the agent's capabilities without exposing real user data, the system is pre-seeded with mock customers. The authentication flow uses a simulated OTP process. When the agent asks for your mobile number and OTP, you can use any of the following pre-seeded accounts:

**1. John Doe**
- **Mobile Number:** `1234567890`
- **OTP:** `1234`
- **Profile:** Has an active Zomato subscription, a wallet balance of $50.0, and several orders in various states (Delayed Pizza Hut, Preparing Burger King, Delivered Starbucks).

**2. Alice Smith**
- **Mobile Number:** `9876543210`
- **OTP:** `1234`
- **Profile:** No active subscription, a wallet balance of $15.5, and orders (Out for Delivery KFC, Cancelled Subway).

## Testing the Application

1. Open the UI at `http://localhost:8501`.
2. Ask "Where is my order?".
3. When prompted, enter the mock mobile number: `1234567890` (This number is seeded with mock data).
4. Enter the mock OTP: `1234`.
5. The agent will authenticate you, link your session, and load your active orders! 
6. Ask the agent things like:
   - *"Tell the driver for my Pizza Hut order to leave it at the door."*
   - *"I was missing garlic bread!"* (Watch the agent automatically file a complaint and refund your wallet).
   - *"What's my wallet balance?"*
   - *"Cancel my Burger King order."*
   - *"Renew my Zomato subscription."*

## Project Structure
- `agent/`: The AI orchestrator microservice. Contains LangChain execution logic, session tracking, and patched tool routing.
- `mock_services/`
  - `data/`: Contains the SQLite database initialization and seeding script (`database.py`) and schema definitions (`models.py`).
  - `zomato_order_service/`: FastAPI microservice managing active orders, driver routing, and complaints.
  - `zomato_user_management_service/`: FastAPI microservice managing authentication, wallets, and subscriptions.
- `frontend/`: Streamlit Chat UI.
- `docker-compose.yml`: Binds the 4 services together over a shared Docker network.
- `deploy.sh`: Primary build and deployment script.
