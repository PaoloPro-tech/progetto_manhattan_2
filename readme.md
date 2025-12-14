@'
# ☢️ Progetto Manhattan

> **Next-Gen Strategic Forecasting System.**
> *Hybrid AI Architecture: Deterministic Forecasting + Cognitive Reasoning.*

![Status](https://img.shields.io/badge/Status-POC_Complete-success)
![Stack](https://img.shields.io/badge/Architecture-API_First-blue)
![AI](https://img.shields.io/badge/AI_Model-GPT--4o-green)

## 📋 Executive Summary
**Progetto Manhattan** non è una semplice dashboard, ma un ecosistema software progettato per potenziare le decisioni degli Account Manager.
Il sistema supera i limiti della BI tradizionale integrando due motori distinti:
1.  **Hard AI (Facebook Prophet):** Analisi matematica delle serie storiche, stagionalità e calcolo del rischio (Intervalli di Confidenza).
2.  **Soft AI (LangGraph + GPT-4o):** Un "consiglio di amministrazione" virtuale che analizza il web in tempo reale e incrocia i dati finanziari con le news di mercato.

---

## 🏗️ Architettura Tecnica (Enterprise Grade)

Il sistema è stato rifattorizzato seguendo il pattern **Decoupled Architecture**:

```mermaid
graph TD
    A[Frontend: Tailwind/AlpineJS] <-->|REST API| B(Backend: FastAPI)
    B <--> C{Orchestrator: LangGraph}
    C <--> D[Agent: Analyst]
    C <--> E[Agent: Researcher]
    C <--> F[Agent: Director]
    B <--> G[Engine: Prophet Forecasting]
    G <--> H[(Data Layer)]
🔹 Backend (Core)
Framework: FastAPI (Python 3.10).
Performance: Asynchronous request handling con Uvicorn.
Documentation: Swagger UI nativa per l'integrazione con sistemi terzi (SAP, Salesforce).
Features:
Endpoint /forecast per calcolo serie temporali.
Endpoint /agent/analyze per la pipeline cognitiva.
Endpoint /agent/chat per sessioni Q&A contestuali.
Generatore PDF server-side con sanificazione input.
🔹 Frontend (UI)
Tech: HTML5, Tailwind CSS, Alpine.js, Chart.js.
Design: Glassmorphism UI (Dark Mode).
UX: Single Page Application (SPA) reattiva, senza ricaricamenti di pagina.
🤖 Il "Cervello" Multi-Agente
Il sistema impiega uno swarm di agenti specializzati orchestrati da LangGraph:
📉 The Quant Analyst:
Analizza i dati grezzi di Prophet.
Identifica trend di crescita (CAGR) e anomalie statistiche.
🌍 The Market Researcher:
Utilizza Tavily AI per scansionare il web in tempo reale.
Filtra fake news e cerca segnali deboli (M&A, cambi management, crisi di settore).
👔 The Strategic Director (GPT-4o):
Sintetizza i dati quantitativi e qualitativi.
Genera azioni commerciali concrete (Upselling, Retention, Crisis Management).
Risponde alle domande dell'utente in chat mantenendo il contesto.
🚀 Quick Start
1. Prerequisiti
Python 3.10+
Chiavi API (OpenAI & Tavily) configurate nel file .env.
2. Installazione
code
Bash
git clone https://github.com/TUO_USERNAME/progetto_manhattan.git
cd progetto_manhattan
pip install -r requirements.txt
3. Avvio del Sistema
Poiché l'architettura è client-server, basta avviare il backend. Il frontend è servito staticamente.
code
Bash
# Avvia il server API
uvicorn app.api.server:app --reload
4. Accesso
Dashboard Strategica: Apri il browser su http://127.0.0.1:8000/dashboard/index.html
Documentazione API (Swagger): http://127.0.0.1:8000/docs
📂 Struttura del Progetto
code
Text
/app
├── /api           # FastAPI Endpoints (REST Interface)
├── /core          # Configurazioni e Prompts di Sistema
├── /data          # Data Layer & Seeder sintetico
├── /services      # Business Logic (Prophet, LangGraph Agent, PDF Engine)
└── /ui            # Frontend Statico (HTML/JS/CSS)
Developed for Akkodis Internal Contest 2025
'@ | Out-File -Encoding utf8 README.md