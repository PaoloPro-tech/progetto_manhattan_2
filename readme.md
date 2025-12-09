@'
# ☢️ Progetto Manhattan

> **Advanced Multi-Agent System for Strategic Forecasting.**
> *Proof of Concept (POC) - Internal Contest 2025*

## 📋 Mission
**Progetto Manhattan** è un'architettura software sperimentale progettata per rivoluzionare il processo decisionale negli account strategici.
Il sistema supera i limiti della Business Intelligence tradizionale fondendo **Analisi Predittiva (Hard AI)** e **Ragionamento Cognitivo (Soft AI)** in un'unica pipeline autonoma.

## 🏗️ Architettura "Hybrid Engine"
Il core del sistema si basa su una separazione netta delle responsabilità:

1.  **The Quantitative Core (Prophet):**
    *   Analisi deterministica delle serie storiche.
    *   Rilevamento stagionalità e trend matematici puri.
    *   Calcolo degli intervalli di confidenza (Risk Assessment).

2.  **The Cognitive Cortex (LangGraph):**
    *   Un grafo di agenti AI autonomi che "leggono" il mondo reale.
    *   **Analyst Agent:** Traduce i numeri in insight di business.
    *   **Researcher Agent:** Esegue scraping etico del web (Tavily) per news in tempo reale.
    *   **Director Agent:** Sintetizza strategie complesse (Upselling, Churn Prevention).

## 🚀 Quick Start

### Requisiti
*   Python 3.10+
*   Accesso API: OpenAI, Tavily

### Installazione
```bash
# 1. Clona il repository
git clone https://github.com/TUO_USERNAME/progetto-manhattan.git
cd progetto-manhattan

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. Configura le chiavi segrete
# Crea un file .env (non incluso nella repo) con:
# OPENAI_API_KEY=sk-...
# TAVILY_API_KEY=tvly-...
code
Bash
# Lancia la dashboard
streamlit run app/main.py
🛠️ Stack Tecnologico
Orchestrator: LangGraph
LLM: GPT-4o / GPT-3.5 Turbo
Forecasting: Facebook Prophet
Frontend: Streamlit Enterprise UI
Search: Tavily AI Search

Developed by ["TeoFil795", "PaoloPro"]
'@ | Out-File -Encoding utf8 README.md