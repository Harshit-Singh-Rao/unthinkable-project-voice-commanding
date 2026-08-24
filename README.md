<div align="center">
  <h1>EchoList</h1>
  <h3>Voice-Activated Shopping Assistant</h3>
</div>

---

## Overview

**EchoList** is a voice-activated shopping list manager built for a modern serverless environment. The frontend is built with **Next.js (React) and Tailwind CSS**, providing a sleek UI that responds to your voice commands. The backend runs as **Python Serverless Functions** on Vercel, handling local ONNX intent classification, entity extraction, and metric arithmetic.

The application is completely **stateless**. User data (shopping lists and purchase histories) is stored entirely client-side using `localStorage`, ensuring privacy and avoiding any database provisioning, making it perfectly suited for free-tier serverless deployments.

---

## Features

- **Voice-First UI**: A dark Next.js interface with a glowing orb that reacts to your voice.
- **English + Hindi**: Hindi commands are normalized to canonical English.
- **Local ONNX Inference**: Intent classification runs inside the Python backend using a compiled ONNX model.
- **Metric Engine & Quantity Caps**: Understands unit arithmetic ("add 200g then 1kg = 1.2kg").
- **Stateless Architecture**: No databases required. The React frontend maintains the state and passes it to the Python API on each request.
- **Trace Panel**: A collapsible panel shows how each command was understood.

---

## Architecture

```mermaid
graph TD
    Client["Next.js UI (React)<br/>Client-side State (localStorage)"]
    Server["Python Serverless API<br/>(/api/command)"]

    Client -- "1. Sends voice text + current state (JSON)" --> Server
    
    subgraph Python Backend
        ONNX["ONNX Intent Classifier"]
        Rules["NLP Entity Extraction"]
    end

    Server --> ONNX
    ONNX --> Rules
    Rules -- "Mutates state" --> Server

    Server -- "2. Returns updated state (JSON)" --> Client
    Client -- "3. Saves to localStorage & Rerenders" --> Client
```

---

## Running Locally

Requirements: Node.js, Python 3.10+

1. Install dependencies:
```bash
npm install
pip install -r requirements.txt
```

2. Run the Next.js development server (which automatically proxies `/api` calls to the local Python backend via `next.config.mjs`):
```bash
npm run dev
# OR simply run npx vercel dev
```

---

## Vercel Deployment

This repository is ready for a 1-click Vercel deployment:
1. Connect your GitHub repository to Vercel.
2. The framework preset should be **Next.js**.
3. Vercel will automatically detect `vercel.json` and install Python dependencies from `requirements.txt` to run the `/api` folder as serverless functions.
4. **No database setup needed.**
