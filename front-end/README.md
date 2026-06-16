# NexoraV3 Front-End 🎨

## 🌟 Overview
The NexoraV3 Front-End is the client interface and embeddable chat widget for the Nexora AI Knowledge Base. It includes an Admin/User Dashboard (React) where users can upload documents and manage their AI knowledge base, as well as a standalone Chat Widget (`widget.iife.js`) that clients can embed on their own websites.

## 🏗️ Final Build & How It Runs Now
The frontend is built as a static Single Page Application (SPA) using React and Vite. In production, it does not require a Node.js server to run. 

Currently, it is deployed on a Contabo server using **CyberPanel (LiteSpeed)**.
- **GitHub Actions** automatically runs `npm run build` on every push to the `main` branch.
- The built static files (from the `dist/` folder) are transferred via SSH directly to the CyberPanel `public_html` directory (`/home/elanka.ai/public_html`).
- CyberPanel natively serves these static files and uses a LiteSpeed reverse proxy (`vhost.conf`) to seamlessly forward all `/api/` traffic to the Dockerized Python backend running on port 8000.

## 🛠️ How to Maintain

### Running Locally on Any PC
1. **Clone the repository:**
   ```bash
   git clone https://github.com/bhanunuwan/elanka_chatbot_frontend.git
   cd elanka_chatbot_frontend
   ```
2. **Install dependencies:**
   Make sure you have Node.js (version 20+) installed.
   ```bash
   npm install
   ```
3. **Run the development server:**
   ```bash
   npm run dev
   ```

### Testing
To test the production build locally before deploying:
```bash
npm run build
npm run preview
```

### Redeploying
Deployment is fully automated through **GitHub Actions**. To redeploy:
1. Make your code changes locally.
2. Commit your changes: `git commit -m "Your update message"`
3. Push to the main branch: `git push origin main`
4. The GitHub Action (`.github/workflows/deploy.yml`) will automatically trigger, build the frontend, and securely transfer the updated files to the CyberPanel server. No manual server intervention is required.

Developer:  **Bhanura** 
> [LinkedIn](https://www.linkedin.com/in/bhanura-waduge-44b7611a7/)
> [GitHub](https://github.com/Bhanura)