# PredictX — Predictive Maintenance & RUL Forecasting Platform

## Overview
An enterprise-ready prognostic maintenance platform leveraging the NASA C-MAPSS dataset. It ingests multi-dimensional sensor streams, identifies irregularities utilizing LSTM Autoencoders, projects remaining useful life (RUL) through an ensembled LSTM-Attention and Prophet architecture, and schedules repairs algorithmically using Mixed-Integer Linear Programming.

## Architecture

```
User Browser
     ↓
Vercel (Frontend — Next.js)
     ↓  HTTP REST API calls
Hugging Face Space (Backend — FastAPI + ML Models)
     ↓
TimescaleDB / MLflow Artifacts / Redis
```

## Project Structure

```
predictive-maintenance/
├── backend/                    # ← Hugging Face Space (FastAPI)
│   ├── app/
│   │   ├── main.py            # FastAPI app with 4 endpoints
│   │   ├── schemas.py         # Pydantic request/response models
│   │   └── inference.py       # ML model inference wrappers
│   ├── Dockerfile             # HF Spaces Docker config
│   ├── requirements.txt
│   └── README.md              # HF Space metadata
│
├── frontend/                   # ← Vercel (Next.js)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout with dark theme
│   │   │   ├── page.tsx       # Dashboard with 5 pages
│   │   │   └── globals.css    # Glassmorphism design system
│   │   └── lib/
│   │       └── api.ts         # API service layer
│   ├── .env.local             # API URL (local dev)
│   ├── .env.example           # Template for production
│   └── vercel.json            # Vercel deployment config
│
├── src/                        # Original ML/pipeline code
├── docker/                     # Infrastructure (Kafka, TimescaleDB, Redis)
└── README.md                   # This file
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Application status validation & cold-start monitoring |
| `POST` | `/predict/anomaly` | Outlier detection utilizing 21 distinct sensor variables |
| `POST` | `/predict/rul` | Remaining useful life projection from time-series context windows |
| `POST` | `/schedule/maintenance` | Automated maintenance planning via MILP optimization |

Interactive API Reference: `<HF_SPACE_URL>/docs`

---

## Deployment Guide

### 1. Backend Integration with Hugging Face Spaces

```bash
# Initialize a fresh Space on huggingface.co/new-space
# Configuration -> SDK: Docker | Visibility: Public

# Upload the backend folder structure
cd backend
git init
git remote add origin https://huggingface.co/spaces/<YOUR_USERNAME>/predictx-api
git add .
git commit -m "Deploy PredictX API"
git push origin main
```

Configure Environment Variables in HF Space Settings:
- `JWT_SECRET` — (optional) Cryptographic key for JWT signatures
- `MODEL_DIR` — Directory mapping for trained ML weights
- `CORS_ORIGINS` — Whitelisted frontend domain addresses

Save your assigned endpoint: `https://<YOUR_USERNAME>-predictx-api.hf.space`

### 2. Frontend Hosting via Vercel

```bash
# Populate local environment parameters with your HF Space endpoint
echo "NEXT_PUBLIC_API_BASE_URL=https://<YOUR_USERNAME>-predictx-api.hf.space" > frontend/.env.local

# Push changes to a GitHub repository, followed by Vercel integration
cd frontend
git init
git remote add origin https://github.com/<YOUR_USERNAME>/predictx-frontend
git add .
git commit -m "Deploy PredictX Frontend"
git push origin main
```

Within the Vercel Control Panel:
- Link the respective GitHub repository
- Compile command: `npm run build`
- Target directory: `.next`
- Inject environment parameter: `NEXT_PUBLIC_API_BASE_URL` = `https://<YOUR_USERNAME>-predictx-api.hf.space`

### 3. Running the Stack Locally

```bash
# Terminal Process 1: Backend Services
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 7860

# Terminal Process 2: Frontend Interface
cd frontend
npm install
npm run dev
```

Dashboard Interface: http://localhost:3000
Backend API Service: http://localhost:7860
Swagger Documentation: http://localhost:7860/docs

---

## Deployment Configuration Checklist

- [ ] Ensure the Hugging Face Space is configured to public and all REST routes are functioning correctly.
- [ ] Confirm the frontend `.env` contains the `NEXT_PUBLIC_API_BASE_URL` mapped to the active HF runtime.
- [ ] Verify the Vercel app is accessible via HTTPS, rendering elements within the 8-second target window.
- [ ] Ensure zero credentials or API keys exist in plain text within tracked source files.
- [ ] Validate CORS configurations to permit Vercel domains executing cross-origin requests to the HF Space.
- [ ] Check that a visual loading indicator correctly triggers while the HF instance handles wake-up delays.
