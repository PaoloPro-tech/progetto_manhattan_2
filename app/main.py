import streamlit as st
import pandas as pd
import time
import sys
import os

# Hack per i percorsi (così non devi settare PYTHONPATH ogni volta)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.forecasting import ForecastingService
from app.services.agent_engine import AgentEngine

# Configurazione Pagina
st.set_page_config(
    page_title="Akkodis Account Intelligence",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom per dare un look "Enterprise"
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # --- Sidebar: Controlli ---
    st.sidebar.title("🔮 Manhattan Project")
    st.sidebar.caption("Akkodis Account Intelligence")
    st.sidebar.markdown("---")
    
    # Carichiamo la lista clienti dal CSV (usando il servizio forecasting per comodità)
    try:
        fs = ForecastingService()
        clienti_disponibili = fs.raw_df["cliente"].unique().tolist()
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return

    selected_client = st.sidebar.selectbox("Seleziona Cliente", clienti_disponibili)
    
    # Recuperiamo il settore (hack veloce dal dataframe)
    sector = fs.raw_df[fs.raw_df["cliente"] == selected_client]["settore"].iloc[0]
    st.sidebar.info(f"📂 Settore: **{sector}**")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 Avvia Analisi Strategica", type="primary"):
        run_analysis_pipeline(selected_client, sector, fs)

def run_analysis_pipeline(client, sector, fs_service):
    """Esegue tutto il flusso: Prophet -> Agenti -> UI"""
    
    # 1. Header
    st.title(f"Analisi Strategica: {client}")
    st.markdown(f"**Data:** {pd.Timestamp.now().strftime('%d/%m/%Y')} | **Status:** Generazione in corso...")
    
    col1, col2 = st.columns([2, 1])
    
    # --- STEP 1: FORECAST QUANTITATIVO ---
    with col1:
        st.subheader("📉 Analisi Serie Storiche (Prophet)")
        with st.spinner("Calcolo proiezioni finanziarie..."):
            try:
                forecast_result = fs_service.generate_forecast(client)
                
                # Mostriamo le metriche in alto
                metrics = forecast_result["metrics"]
                m1, m2, m3 = st.columns(3)
                m1.metric("Previsione Fatturato", f"€ {metrics['previsione_prossimo_anno']:,.0f}")
                m2.metric("Trend", metrics['trend_di_fondo'], delta=f"{metrics['crescita_percentuale']}%")
                m3.metric("Affidabilità", "Alta" if metrics['confidenza_min'] > 0 else "Media")
                
                # Mostriamo il grafico
                st.plotly_chart(forecast_result["plot"], use_container_width=True)
                
            except Exception as e:
                st.error(f"Errore nel forecasting: {e}")
                st.stop()

    # --- STEP 2: AGENTI COGNITIVI ---
    with col2:
        st.subheader("🧠 Elaborazione Cognitiva")
        engine = AgentEngine()
        
        # Container per i log in tempo reale
        status_container = st.status("Attivazione Agenti AI...", expanded=True)
        
        try:
            # 1. Analista
            status_container.write("🤖 **Analista:** Interpretazione dati matematici...")
            # Simuliamo un piccolo delay per effetto scenico (rimuovibile)
            time.sleep(1) 
            
            # Lanciamo il grafo
            result = engine.run_analysis(client, sector, metrics)
            
            status_container.write("🌍 **Ricercatore:** Scansione news globali (Tavily)...")
            status_container.write("👔 **Direttore:** Sintesi strategia finale...")
            
            status_container.update(label="Analisi Completata!", state="complete", expanded=False)
            
            # Mostriamo i dettagli intermedi (Espandibili)
            with st.expander("Dettaglio Analisi Dati (Internal)"):
                st.markdown(result["analyst_output"])
                
            with st.expander("Dettaglio Ricerca Mercato (External)"):
                st.markdown(result["researcher_output"])
                
        except Exception as e:
            status_container.update(label="Errore negli Agenti", state="error")
            st.error(f"Errore AI: {e}")
            st.stop()

    # --- STEP 3: REPORT FINALE ---
# --- STEP 3: REPORT FINALE ---
    st.markdown("---")
    st.header("📑 Report Strategico Finale")
    
    # MODIFICA QUI: Ho aggiunto 'color: #0f172a' per forzare il testo scuro
    st.markdown(f"""
    <div style="
        background-color: #e8f4f8; 
        color: #0f172a;
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #b3d7ff;
        font-family: sans-serif;
    ">
        {result['final_report']}
    </div>
    """, unsafe_allow_html=True)
    
if __name__ == "__main__":
    main()