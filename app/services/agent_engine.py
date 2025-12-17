import os
from typing import TypedDict, Optional
from dotenv import load_dotenv

# Carica esplicitamente le variabili d'ambiente subito
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langchain_community.tools.tavily_search import TavilySearchResults

# Importiamo i nostri prompt puliti e le config
from app.core.prompts import ANALYST_SYSTEM_PROMPT, RESEARCHER_SYSTEM_PROMPT, DIRECTOR_SYSTEM_PROMPT
from app.core.config import settings

# ✅ RAG Service (Repo-based)
from app.services.rag_service import RAGService


# --- 1. Definizione dello Stato ---
class AgentState(TypedDict):
    client_name: str
    sector: str
    financial_metrics: dict  # Output di Prophet

    # Output degli agenti
    analyst_output: Optional[str]
    internal_research_output: Optional[str]   # ✅ nuovo
    researcher_output: Optional[str]
    final_report: Optional[str]


class AgentEngine:
    def __init__(self):
        # Inizializziamo il modello LLM
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-5-mini-2025-08-07",
            temperature=0
        )

        # Tool di ricerca web (Tavily)
        self.search_tool = TavilySearchResults(
            tavily_api_key=settings.TAVILY_API_KEY,
            k=3
        )

        # ✅ RAG interno (repo indicizzato in Chroma)
        # Nota: se la directory/collection non esiste ancora, il nodo gestirà l'errore in modo "soft".
        self.rag = RAGService(
            persist_dir=settings.RAG_PERSIST_DIR,
            collection_name=settings.RAG_COLLECTION_NAME,
            top_k=settings.RAG_TOP_K
        )

    # --- 2. Definizione dei Nodi (Gli Agenti) ---

    def analyst_node(self, state: AgentState):
        """L'Analista guarda i numeri JSON e scrive un commento"""
        print(f"   ... 🤖 Analista al lavoro su {state['client_name']} ...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYST_SYSTEM_PROMPT),
            ("user", "Ecco le metriche finanziarie: {metrics}")
        ])
        chain = prompt | self.llm | StrOutputParser()

        metrics_str = str(state["financial_metrics"])
        result = chain.invoke({"metrics": metrics_str})

        return {"analyst_output": result}

    def internal_researcher_node(self, state: AgentState):
        """Ricerca interna via RAG (repo indicizzato in Chroma)"""
        print(f"   ... 🏢 Ricerca interna (RAG) su {state['client_name']} ...")

        query = (
            f"{state['client_name']} {state['sector']}. "
            f"Cerca informazioni interne rilevanti (progetti, note, offerte, rischi, punti di forza)."
        )

        # Proviamo a recuperare documenti dal vector store
        try:
            docs = self.rag.retrieve(query)

            if docs:
                context = "\n\n".join(
                    [f"[{d.metadata.get('source','unknown')}]\n{d.page_content}" for d in docs]
                )
            else:
                context = "NESSUN CONTENUTO RECUPERATO."
        except Exception as e:
            # Gestione “soft”: non blocca il workflow, ma informa nel report
            context = (
                "RICERCA INTERNA NON DISPONIBILE.\n"
                f"Dettaglio errore: {str(e)}\n"
                "Suggerimento: assicurati di aver eseguito l'indicizzazione (python -m app.data.rag_index_repo) "
                "e che RAG_PERSIST_DIR punti alla directory corretta."
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Sei un ricercatore interno. Usa SOLO il contesto. Se non trovi dati, dillo chiaramente."),
            ("user",
             "DOMANDA:\n{q}\n\n"
             "CONTESTO (con fonti tra []):\n{ctx}\n\n"
             "Rispondi in italiano e cita sempre le fonti tra [] quando usi informazioni.")
        ])

        chain = prompt | self.llm | StrOutputParser()
        out = chain.invoke({"q": query, "ctx": context})

        return {"internal_research_output": out}

    def researcher_node(self, state: AgentState):
        """Il Ricercatore usa Tavily per cercare news"""
        print(f"   ... 🌍 Ricercatore sta scansionando il web per {state['client_name']} ...")

        query = f"Latest business news and financial trends for {state['client_name']} in {state['sector']} sector"

        try:
            # Invoca il tool di ricerca
            search_results = self.search_tool.invoke(query)
            # Formatta i risultati
            content = "\n".join([f"- {res['content']} (Fonte: {res['url']})" for res in search_results])
        except Exception as e:
            content = f"Nessuna news trovata o errore API: {str(e)}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", RESEARCHER_SYSTEM_PROMPT),
            ("user", "Ecco i risultati grezzi della ricerca: {raw_data}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        final_summary = chain.invoke({"raw_data": content})

        return {"researcher_output": final_summary}

    def director_node(self, state: AgentState):
        """Il Direttore legge tutto e decide"""
        print("   ... 👔 Il Direttore sta scrivendo la strategia ...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", DIRECTOR_SYSTEM_PROMPT),
            ("user", """
            CLIENTE: {client}

            REPORT ANALISTA (Dati Interni):
            {analyst_doc}

            REPORT RICERCA INTERNA (Repo RAG):
            {internal_doc}

            REPORT RICERCATORE (News Esterne):
            {researcher_doc}
            """)
        ])
        chain = prompt | self.llm | StrOutputParser()

        final_report = chain.invoke({
            "client": state["client_name"],
            "analyst_doc": state["analyst_output"],
            "internal_doc": state["internal_research_output"],
            "researcher_doc": state["researcher_output"]
        })

        return {"final_report": final_report}

    # --- 3. Costruzione del Grafo ---
    def build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("analyst", self.analyst_node)
        workflow.add_node("internal_researcher", self.internal_researcher_node)  # ✅ nuovo
        workflow.add_node("researcher", self.researcher_node)
        workflow.add_node("director", self.director_node)

        workflow.set_entry_point("analyst")
        workflow.add_edge("analyst", "internal_researcher")       # ✅ nuovo
        workflow.add_edge("internal_researcher", "researcher")    # ✅ nuovo
        workflow.add_edge("researcher", "director")
        workflow.add_edge("director", END)

        return workflow.compile()

    def run_analysis(self, client: str, sector: str, metrics: dict):
        app = self.build_graph()

        inputs = {
            "client_name": client,
            "sector": sector,
            "financial_metrics": metrics,
            "analyst_output": None,
            "internal_research_output": None,  # ✅ nuovo
            "researcher_output": None,
            "final_report": None
        }

        return app.invoke(inputs)

    def chat_with_director(self, user_question: str, context_report: str):
        """
        Permette di fare Q&A sul report generato.
        Usa il report finale come contesto per rispondere.
        """
        print(f"   ... 💬 Chat in corso: {user_question} ...")

        system_prompt = """
        Sei il Direttore Strategico di Akkodis.
        Hai appena redatto un report strategico per un cliente (che ti fornisco come contesto).

        L'Account Manager ti sta facendo domande di approfondimento.
        Rispondi in modo professionale, sintetico e basandoti ESCLUSIVAMENTE sui dati del report.
        Se la domanda è fuori contesto, rispondi che non hai dati a riguardo.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", f"CONTESTO REPORT:\n{context_report}\n\nDOMANDA ACCOUNT MANAGER:\n{user_question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({})

        return response


# Test locale
if __name__ == "__main__":
    mock_metrics = {
        "crescita_percentuale": 12.5,
        "trend_di_fondo": "Crescente",
        "previsione_prossimo_anno": 150000
    }

    try:
        engine = AgentEngine()
        print("🚀 Avvio Simulazione Agenti...")
        outcome = engine.run_analysis("Leonardo", "Aerospace", mock_metrics)
        print("\n=== REPORT FINALE ===")
        print(outcome["final_report"])
    except Exception as e:
        print(f"❌ Errore critico: {e}")
