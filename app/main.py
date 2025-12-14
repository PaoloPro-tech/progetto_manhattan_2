import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

# CONFIGURAZIONE API
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Progetto Manhattan", page_icon="☢️", layout="wide")

# CSS Custom
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .report-box { background-color: #f0f2f6; color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #d1d5db; }
    /* Chat bubbles */
    .chat-user { background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin-bottom: 5px; text-align: right; color: #0d47a1; }
    .chat-bot { background-color: #f1f8e9; padding: 10px; border-radius: 10px; margin-bottom: 5px; color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# --- Inizializzazione Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "final_report_context" not in st.session_state:
    st.session_state.final_report_context = ""
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

def fetch_clients():
    try:
        resp = requests.get(f"{API_URL}/clients")
        if resp.status_code == 200:
            return resp.json()["clients"]
        return []
    except:
        return []

def plot_forecast_from_json(forecast_data, client_name):
    df = pd.DataFrame(forecast_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['ds'], y=df['yhat'], mode='lines', name='Previsione', line=dict(color='#007bff', width=3)))
    fig.add_trace(go.Scatter(
        x=pd.concat([df['ds'], df['ds'][::-1]]),
        y=pd.concat([df['yhat_upper'], df['yhat_lower'][::-1]]),
        fill='toself', fillcolor='rgba(0,123,255,0.2)', line=dict(color='rgba(255,255,255,0)'), name='Confidenza'
    ))
    fig.update_layout(title=f"Forecast Strategico: {client_name}", xaxis_title="Timeline", yaxis_title="Fatturato (€)", template="plotly_white", height=400)
    return fig

def main():
    # --- SIDEBAR ---
    st.sidebar.title("☢️ Manhattan")
    st.sidebar.caption("API-First Architecture")
    
    st.sidebar.subheader("📂 Dati Sorgente")
    uploaded_file = st.sidebar.file_uploader("Carica CSV Aziendale", type="csv")
    if uploaded_file:
        with st.spinner("Upload..."):
            files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
            try:
                requests.post(f"{API_URL}/upload-data", files=files)
                st.sidebar.success("✅ Upload OK")
            except:
                st.sidebar.error("Backend Offline")

    st.sidebar.markdown("---")
    clienti = fetch_clients()
    if not clienti:
        st.error("Backend Offline. Avvia uvicorn!")
        st.stop()
        
    selected_client = st.sidebar.selectbox("Seleziona Cliente", clienti)
    sector_map = {"Leonardo": "Aerospace", "Stellantis": "Automotive", "Ferrari": "Luxury", "Gucci": "Fashion"}
    sector = sector_map.get(selected_client, "General Industry")
    
    if st.sidebar.button("🚀 Lancia Analisi Completa", type="primary"):
        # Reset stato quando si lancia una nuova analisi
        st.session_state.chat_history = []
        st.session_state.final_report_context = ""
        st.session_state.analysis_done = False
        run_dashboard(selected_client, sector)

    # Se l'analisi è stata fatta, mostriamo la UI persistente (così la chat non sparisce)
    if st.session_state.analysis_done:
        render_persistent_ui(selected_client)

def run_dashboard(client, sector):
    # Logica di calcolo (eseguita una volta sola al click)
    metrics = None
    
    with st.spinner("⏳ Elaborazione Prophet & Agenti..."):
        try:
            # 1. Forecast
            payload = {"client_name": client, "months": 12}
            resp = requests.post(f"{API_URL}/forecast", json=payload)
            if resp.status_code != 200:
                st.error("Errore Forecast")
                return
            data = resp.json()
            metrics = data["metrics"]
            st.session_state.forecast_data = data["forecast_data"]
            st.session_state.metrics = metrics

            # 2. Agenti
            agent_payload = {"client_name": client, "sector": sector, "metrics": metrics}
            agent_resp = requests.post(f"{API_URL}/agent/analyze", json=agent_payload)
            if agent_resp.status_code != 200:
                st.error("Errore Agenti")
                return
            
            agent_data = agent_resp.json()
            st.session_state.agent_data = agent_data
            # Salviamo il report per il contesto della chat
            st.session_state.final_report_context = agent_data["final_report"]
            st.session_state.analysis_done = True
            
        except Exception as e:
            st.error(f"Errore Critico: {e}")

def render_persistent_ui(client):
    """Renderizza la dashboard usando i dati salvati in Session State"""
    st.title(f"Dashboard Strategica: {client}")
    
    col1, col2 = st.columns([6, 4])
    
    # --- COLONNA 1: DATI ---
    with col1:
        st.subheader("📉 Proiezione Finanziaria")
        metrics = st.session_state.metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Previsione FY2026", f"€ {metrics['previsione_prossimo_anno']:,.0f}")
        c2.metric("Growth Rate", f"{metrics['crescita_percentuale']}%", delta=metrics['trend_di_fondo'])
        c3.metric("Confidence", "High" if metrics['confidenza_min'] > 0 else "Low")
        
        fig = plot_forecast_from_json(st.session_state.forecast_data, client)
        st.plotly_chart(fig, use_container_width=True)

    # --- COLONNA 2: AGENTI ---
    with col2:
        st.subheader("🧠 Report Agenti")
        agent_data = st.session_state.agent_data
        
        with st.expander("📝 Insight Interni & Esterne"):
            st.info(agent_data["analyst_output"])
            st.success(agent_data["researcher_output"])
            
        st.markdown(f"""
        <div class="report-box">
            <h4>👔 Direttore Strategico</h4>
            {agent_data['final_report']}
        </div>
        """, unsafe_allow_html=True)
    
        # --- BOTTONE DOWNLOAD PDF ---
        st.markdown("###") # Spaziatura
        if st.button("📥 Genera PDF Ufficiale"):
            with st.spinner("Impaginazione PDF in corso..."):
                try:
                    pdf_payload = {
                        "client_name": client,
                        "sector": "Strategy", # O recuperalo dallo stato se vuoi
                        "report_text": agent_data['final_report']
                    }
                    resp = requests.post(f"{API_URL}/report/pdf", json=pdf_payload)
                    
                    if resp.status_code == 200:
                        st.download_button(
                            label="📄 Clicca qui per scaricare il PDF",
                            data=resp.content,
                            file_name=f"Report_Strategico_{client}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error(f"Errore Backend: {resp.text}")
                except Exception as e:
                    st.error(f"Errore: {e}")

    # --- SEZIONE CHAT ---
    st.markdown("---")
    st.subheader("💬 Parla con il Direttore Strategico")
    
    # Mostra cronologia
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 <b>Tu:</b> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bot">👔 <b>Direttore:</b> {msg["content"]}</div>', unsafe_allow_html=True)

    # Input Chat
    if prompt := st.chat_input("Chiedi dettagli sulla strategia... (es: 'Perché suggerisci upselling?')"):
        # 1. Aggiungi messaggio utente
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # 2. Chiama API Backend
        with st.spinner("Il Direttore sta riflettendo..."):
            try:
                chat_payload = {
                    "question": prompt,
                    "context_report": st.session_state.final_report_context
                }
                resp = requests.post(f"{API_URL}/agent/chat", json=chat_payload)
                if resp.status_code == 200:
                    answer = resp.json()["answer"]
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    st.rerun() # Ricarica per mostrare il nuovo messaggio
                else:
                    st.error("Errore API Chat")
            except Exception as e:
                st.error(f"Errore connessione: {e}")

if __name__ == "__main__":
    main()