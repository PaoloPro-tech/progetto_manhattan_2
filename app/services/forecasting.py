import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly
import json
import plotly.graph_objects as go
from typing import Dict, Any, Tuple

class ForecastingService:
    """
    Servizio Enterprise per la gestione delle serie temporali.
    Incapsula la logica di Facebook Prophet per renderla agnostica all'UI.
    """

    def __init__(self, data_path: str = "app/data/storico_commesse.csv"):
        self.data_path = data_path
        # Carichiamo il dataset una volta sola all'inizializzazione
        self.raw_df = pd.read_csv(data_path)

    def _prepare_data(self, client_name: str) -> pd.DataFrame:
        """Filtra i dati per cliente e li formatta per Prophet (ds, y)"""
        
        # Filtriamo per cliente
        df_client = self.raw_df[self.raw_df["cliente"] == client_name].copy()
        
        if df_client.empty:
            raise ValueError(f"Nessun dato trovato per il cliente: {client_name}")

        # Prophet vuole tassativamente due colonne: 'ds' (data) e 'y' (valore)
        df_prophet = df_client[["data_commessa", "fatturato"]].rename(
            columns={"data_commessa": "ds", "fatturato": "y"}
        )
        
        return df_prophet

    def generate_forecast(self, client_name: str, months: int = 12) -> Dict[str, Any]:
        """
        Esegue il training on-the-fly e genera la predizione.
        Restituisce un dizionario con:
        - Il grafico Plotly (oggetto JSON)
        - I KPI numerici (per l'Agente AI)
        """
        
        # 1. Preparazione Dati
        df = self._prepare_data(client_name)
        
        # 2. Configurazione Modello
        # yearly_seasonality=True forza Prophet a cercare pattern annuali
        model = Prophet(yearly_seasonality=True, daily_seasonality=False, weekly_seasonality=False)
        
        # 3. Training
        model.fit(df)
        
        # 4. Predizione
        future = model.make_future_dataframe(periods=months, freq='M')
        forecast = model.predict(future)
        
        # 5. Estrazione KPI per l'IA (Analista Quantitativo)
        # Prendiamo gli ultimi 12 mesi storici e i 12 predetti
        last_history_val = df['y'].iloc[-12:].sum()
        predicted_val = forecast['yhat'].iloc[-months:].sum()
        
        growth_pct = ((predicted_val - last_history_val) / last_history_val) * 100
        
        # Trend dell'ultimo mese previsto
        trend_direction = "Crescente" if forecast['trend'].iloc[-1] > forecast['trend'].iloc[0] else "Decrescente"

        kpi_metrics = {
            "storico_ultimo_anno": round(last_history_val, 2),
            "previsione_prossimo_anno": round(predicted_val, 2),
            "crescita_percentuale": round(growth_pct, 2),
            "trend_di_fondo": trend_direction,
            "confidenza_min": round(forecast['yhat_lower'].iloc[-1], 2), # Worst case
            "confidenza_max": round(forecast['yhat_upper'].iloc[-1], 2)  # Best case
        }

        # 6. Generazione Grafico Interattivo
        fig = plot_plotly(model, forecast)
        fig.update_layout(
            title=f"Forecast Fatturato: {client_name}",
            xaxis_title="Data",
            yaxis_title="Fatturato (€)",
            template="plotly_white"
        )

        return {
            "plot": fig,        # Oggetto grafico per Streamlit
            "metrics": kpi_metrics, # Dati puri per LangGraph
            "raw_forecast": forecast # DataFrame completo (opzionale)
        }

# Esempio di utilizzo locale (per debug)
if __name__ == "__main__":
    service = ForecastingService()
    try:
        # Testiamo con Leonardo (che nel seeder ha trend positivo)
        result = service.generate_forecast("Leonardo")
        print("✅ Forecast Generato!")
        print("📊 KPI estratti per l'AI:")
        print(json.dumps(result["metrics"], indent=2))
    except Exception as e:
        print(f"❌ Errore: {e}")