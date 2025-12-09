import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Clienti target per la POC
CLIENTI = [
    {"name": "Stellantis", "sector": "Automotive", "trend": 1.05, "volatility": 0.05}, # Crescita lenta
    {"name": "Leonardo", "sector": "Aerospace", "trend": 1.15, "volatility": 0.03},   # Crescita forte, stabile
    {"name": "Ferrari", "sector": "Luxury Auto", "trend": 1.10, "volatility": 0.02},  # Molto stabile
    {"name": "Brunello Cucinelli", "sector": "Fashion", "trend": 1.40, "volatility": 0.15}, # In crescita, volatile
    {"name": "Gucci", "sector": "Fashion", "trend": 0.85, "volatility": 0.15} # In calo, volatile
]

def generate_realistic_series(start_date, months=36, base_value=50000, trend_factor=1.0, volatility=0.05):
    """
    Genera una serie temporale con:
    1. Trend lineare (crescita/decrescita)
    2. Stagionalità (picco a Dicembre, calo ad Agosto)
    3. Rumore casuale (volatility)
    """
    dates = []
    values = []
    
    current_date = start_date
    
    for i in range(months):
        # 1. Componente Trend
        # Aumenta o diminuisce progressivamente ogni mese
        trend_component = base_value * (1 + (trend_factor - 1) * (i / months))
        
        # 2. Componente Stagionalità (Simulata con seno)
        # Agosto (mese 8) basso, Dicembre (mese 12) alto
        month_idx = current_date.month
        if month_idx == 8: # Agosto
            seasonality = 0.6 
        elif month_idx == 12: # Dicembre
            seasonality = 1.4
        elif month_idx in [6, 7]: # Estate pre-agosto
            seasonality = 0.9
        else:
            seasonality = 1.0 + np.random.uniform(-0.05, 0.05)
            
        # 3. Componente Random (Rumore)
        noise = np.random.normal(0, volatility * base_value)
        
        final_value = (trend_component * seasonality) + noise
        
        # Ensure no negative values
        final_value = max(final_value, 0)
        
        dates.append(current_date)
        values.append(round(final_value, 2))
        
        # Vai al prossimo mese (semplificato 30gg)
        current_date += timedelta(days=30)
        
    return dates, values

def main():
    print("🌱 Generazione dati sintetici in corso...")
    
    all_data = []
    start_date = datetime(2022, 1, 15) # Partiamo da 3 anni fa
    
    for client in CLIENTI:
        dates, revenues = generate_realistic_series(
            start_date=start_date,
            months=48, # 36 storici + 12 futuri (per testare noi, ma salveremo tutto)
            base_value=np.random.randint(40000, 80000),
            trend_factor=client["trend"],
            volatility=client["volatility"]
        )
        
        for d, r in zip(dates, revenues):
            all_data.append({
                "data_commessa": d.strftime("%Y-%m-%d"),
                "cliente": client["name"],
                "settore": client["sector"],
                "fatturato": r,
                # Aggiungiamo margine finto
                "margine_pct": round(np.random.uniform(10, 25), 1)
            })
            
    df = pd.DataFrame(all_data)
    
    # Salviamo nella cartella data
    output_path = "app/data/storico_commesse.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ Dataset creato con successo: {output_path}")
    print(f"   Totale righe: {len(df)}")
    print(df.head())

if __name__ == "__main__":
    main()