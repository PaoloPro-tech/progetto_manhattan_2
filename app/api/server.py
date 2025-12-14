# app/api/server.py
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import io
import sys
import os
from fastapi.responses import Response
from app.services.pdf_generator import PDFReportGenerator

# Aggiungiamo la root al path per sicurezza
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.forecasting import ForecastingService
from app.services.agent_engine import AgentEngine

app = FastAPI(
    title="Progetto Manhattan API",
    description="Backend Enterprise per Forecasting Strategico Multi-Agente",
    version="1.0.0"
)

# --- DTOs (Data Transfer Objects) ---
class ForecastRequest(BaseModel):
    client_name: str
    months: int = 12

class AnalysisRequest(BaseModel):
    client_name: str
    sector: str
    # Le metriche sono opzionali, se non ci sono le ricalcoliamo
    metrics: dict = None 

class ChatRequest(BaseModel):
    question: str
    context_report: str  # Il testo del report su cui basare la risposta

class ReportRequest(BaseModel):
    client_name: str
    sector: str
    report_text: str

# --- Endpoints ---

@app.post("/agent/chat")
def chat_agent(req: ChatRequest):
    try:
        engine = AgentEngine()
        # Qui il Server CHIAMA il Cervello
        answer = engine.chat_with_director(req.question, req.context_report)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "active", "system": "Manhattan Core v1.0"}

@app.get("/clients")
def get_clients():
    """Restituisce la lista dei clienti disponibili nel dataset"""
    try:
        fs = ForecastingService()
        clients = fs.raw_df["cliente"].unique().tolist()
        return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast")
def generate_forecast(req: ForecastRequest):
    """Esegue Prophet e restituisce JSON puro"""
    try:
        fs = ForecastingService()
        result = fs.generate_forecast(req.client_name, req.months)
        
        # Estraiamo i dati per il grafico (frontend deve disegnarlo)
        forecast_df = result["raw_forecast"][['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(req.months + 12)
        
        return {
            "metrics": result["metrics"],
            "forecast_data": forecast_df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/analyze")
def run_agent(req: AnalysisRequest):
    """Lancia la pipeline LangGraph"""
    try:
        # Se il frontend non passa le metriche, le calcoliamo al volo
        metrics = req.metrics
        if not metrics:
            fs = ForecastingService()
            f_res = fs.generate_forecast(req.client_name)
            metrics = f_res["metrics"]

        engine = AgentEngine()
        result = engine.run_analysis(req.client_name, req.sector, metrics)
        
        return {
            "analyst_output": result["analyst_output"],
            "researcher_output": result["researcher_output"],
            "final_report": result["final_report"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-data")
async def upload_csv(file: UploadFile = File(...)):
    """Endpoint per caricare CSV custom"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Il file deve essere un CSV")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Check colonne minime
        required = {'data_commessa', 'cliente', 'settore', 'fatturato'}
        if not required.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"CSV mancante di colonne: {required}")
        
        # Salviamo come file custom
        df.to_csv("app/data/custom_upload.csv", index=False)
        return {"message": "Upload completato", "rows": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/report/pdf")
def generate_pdf(req: ReportRequest):
    """Genera il PDF al volo e lo restituisce come file binario"""
    try:
        pdf_gen = PDFReportGenerator(req.client_name, req.sector)
        pdf_gen.add_content(req.report_text)
        
        # Ottiene i byte del PDF
        # Converte il bytearray in bytes immutabili
        pdf_bytes = bytes(pdf_gen.output(dest='S'))
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Report_{req.client_name}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))