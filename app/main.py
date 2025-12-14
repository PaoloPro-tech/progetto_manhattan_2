import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time
import json

# CONFIGURAZIONE API
# Se un domani metti il backend su Azure, cambi solo questa stringa!
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Progetto Manhattan", page_icon="☢️", layout="wide")

# CSS Custom
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .report-box { background-color: #f0f2f6; color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #d1d5db; }
</style>
""", unsafe_allow_html=True)

def fetch_clients():
    """Chiede all'API la lista dei clienti"""
    try:
        resp = requests.get(f"{API_URL}/clients")
        if resp.status_code == 200:
            return resp.json()["clients"]
        return []
    except:
        st.error("⚠️ Impossibile connettersi al Backend API. Assicurati che uvicorn sia attivo!")
        return []

def plot_forecast_from_json(forecast_data, client_name):
    """Ricostruisce il grafico Plotly dai dati JSON ricevuti dall'API"""
    df = pd.DataFrame(forecast_data)
    
    fig = go.Figure()
    
    # 1. Linea principale (Predizione)
    fig.add_trace(go.Scatter(
        x=df['ds'], y=df['yhat'],
        mode='lines', name='Previsione',
        line=dict(color='#007bff', width=3)
    ))
    
    # 2. Intervallo di confidenza (Area ombreggiata)
    fig.add_trace(go.Scatter(
        x=pd.concat([df['ds'], df['ds'][::-1]]),
        y=pd.concat([df['yhat_upper'], df['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(0,123,255,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidenza'
    ))
    
    fig.update_layout(
        title=f"Forecast Strategico: {client_name}",
        xaxis_title="Timeline",
        yaxis_title="Fatturato Previsto (€)",
        template="plotly_white",
        height=400
    )
    return fig

def main():
    # --- SIDEBAR ---
    st.sidebar.title("☢️ Manhattan")
    st.sidebar.caption("API-First Architecture")
    
    # 1. Sezione Upload (SCALABILITÀ)
    st.sidebar.subheader("📂 Dati Sorgente")
    uploaded_file = st.sidebar.file_uploader("Carica CSV Aziendale", type="csv")
    
    if uploaded_file:
        with st.spinner("Caricamento dati al Backend..."):
            files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
            try:
                resp = requests.post(f"{API_URL}/upload-data", files=files)
                if resp.status_code == 200:
                    st.sidebar.success(f"✅ Upload OK! ({resp.json()['rows']} righe)")
                else:
                    st.sidebar.error("Errore Upload")
            except Exception as e:
                st.sidebar.error(f"Backend offline: {e}")

    st.sidebar.markdown("---")
    
    # 2. Selezione Cliente
    clienti = fetch_clients()
    if not clienti:
        st.warning("Backend non raggiungibile.")
        st.stop()
        
    selected_client = st.sidebar.selectbox("Seleziona Cliente", clienti)
    
    # Settore (Hardcoded per semplicità nella UI, o potremmo chiederlo all'API)
    # Per la demo va bene così o si può migliorare l'endpoint /clients per restituire anche il settore
    sector_map = {"Leonardo": "Aerospace", "Stellantis": "Automotive", "Ferrari": "Luxury", "Gucci": "Fashion"}
    sector = sector_map.get(selected_client, "General Industry")
    
    if st.sidebar.button("🚀 Lancia Analisi Completa", type="primary"):
        run_dashboard(selected_client, sector)

def run_dashboard(client, sector):
    st.title(f"Dashboard Strategica: {client}")
    st.markdown(f"**Target Sector:** {sector} | **Engine:** Prophet + GPT-4o")
    
    col1, col2 = st.columns([6, 4])
    
    # Variabili per conservare i dati tra le colonne
    metrics = None
    
    # --- COLONNA 1: DATI QUANTITATIVI (API /forecast) ---
    with col1:
        st.subheader("📉 Proiezione Finanziaria")
        with st.spinner("Richiesta al Neural Engine (Prophet)..."):
            try:
                payload = {"client_name": client, "months": 12}
                resp = requests.post(f"{API_URL}/forecast", json=payload)
                
                if resp.status_code == 200:
                    data = resp.json()
                    metrics = data["metrics"]
                    forecast_raw = data["forecast_data"]
                    
                    # Visualizza Metriche
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Previsione FY2026", f"€ {metrics['previsione_prossimo_anno']:,.0f}")
                    c2.metric("Growth Rate", f"{metrics['crescita_percentuale']}%", delta=metrics['trend_di_fondo'])
                    c3.metric("Confidence", "High" if metrics['confidenza_min'] > 0 else "Low")
                    
                    # Disegna Grafico
                    fig = plot_forecast_from_json(forecast_raw, client)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Errore API Forecast: {resp.text}")
                    st.stop()
            except Exception as e:
                st.error(f"Connection Error: {e}")
                st.stop()

    # --- COLONNA 2: AGENTI COGNITIVI (API /agent/analyze) ---
    with col2:
        st.subheader("🧠 Analisi Agenti Autonomi")
        
        status_box = st.status("Inizializzazione swarm di agenti...", expanded=True)
        
        try:
            status_box.write("📡 Handshake con API Backend...")
            
            # Chiamata API Agenti
            agent_payload = {
                "client_name": client, 
                "sector": sector,
                "metrics": metrics # Passiamo le metriche calcolate prima
            }
            
            status_box.write("🕵️ Analista & Ricercatore al lavoro...")
            agent_resp = requests.post(f"{API_URL}/agent/analyze", json=agent_payload)
            
            if agent_resp.status_code == 200:
                agent_data = agent_resp.json()
                status_box.update(label="Analisi Completata", state="complete", expanded=False)
                
                # Tab per vedere i dettagli
                tab1, tab2 = st.tabs(["📝 Insight Interni", "🌍 News Esterne"])
                with tab1:
                    st.info(agent_data["analyst_output"])
                with tab2:
                    st.success(agent_data["researcher_output"])
                
                # Report Finale
                st.markdown("### 👔 Direttore Strategico")
                st.markdown(f"""
                <div class="report-box">
                    {agent_data['final_report']}
                </div>
                """, unsafe_allow_html=True)
                
            else:
                status_box.update(label="Errore Agenti", state="error")
                st.error(agent_resp.text)
                
        except Exception as e:
            st.error(f"Errore critico: {e}")

if __name__ == "__main__":
    main()