# NexoraV3 Back-End 🤖

## 🌟 Overview
NexoraV3 Back-End is an intelligent, multi-tenant AI knowledge base built with FastAPI and Python. It features:
- **Intelligent Web Crawling** and Multi-Format Document Processing (PDF, DOCX, HTML).
- **Vector Search & RAG** utilizing local sentence-transformers (384-dimensional) and Google Gemini 2.5 Flash for context-aware conversational AI.
- **Multi-Tenant REST API** with JWT authentication, ensuring secure user management and per-user data isolation.

## 🏗️ Final Build & How It Runs Now
The backend is fully containerized using Docker and is orchestrated via `docker-compose`. 

Currently, it runs on a Contabo server alongside CyberPanel:
- The system is composed of three Docker containers: **FastAPI (Backend)**, **MongoDB (Storage)**, and **Qdrant (Vector Database)**.
- The backend container exposes port `8000` to the server's localhost.
- CyberPanel's LiteSpeed web server uses an `extprocessor` and `context` reverse proxy to securely route public traffic from `https://elanka.ai/api` directly into the Docker backend container.
- Deployment is automated via GitHub Actions, which builds the new Docker image and restarts the containers automatically on code push.

## 🛠️ How to Maintain

### Running Locally on Any PC
1. **Clone the repository:**
   ```bash
   git clone https://github.com/bhanunuwan/elanka_chatbot_backend.git
   cd elanka_chatbot_backend
   ```
2. **Configure Environment:**
   Create a `.env` file in the root directory based on the expected variables (e.g., MongoDB credentials, Google Gemini API Key, JWT Secret).
3. **Run via Docker (Recommended):**
   Ensure Docker Desktop is installed and running.
   ```bash
   docker compose up -d --build
   ```
4. **Access the API:**
   The API will be available at `http://localhost:8000`. You can view the Swagger UI documentation at `http://localhost:8000/docs`.

### Testing
To test the API endpoints locally, use the provided Postman collection (`Nexora001_API.postman_collection.json`) or navigate to the built-in Swagger documentation (`/docs`) in your browser to interact with the endpoints.

### Redeploying
Deployment is fully automated through **GitHub Actions**. To redeploy:
1. Make your code changes locally.
2. Commit your changes: `git commit -m "Your update message"`
3. Push to the main branch: `git push origin main`
4. The GitHub Action (`.github/workflows/deploy.yml`) will automatically trigger. It will SSH into the server, run `docker compose build`, and `docker compose up -d` to seamlessly restart the updated containers with zero-configuration required.

Developer:  **Bhanura** 
> [LinkedIn](https://www.linkedin.com/in/bhanura-waduge-44b7611a7/)
> [GitHub](https://github.com/Bhanura)

