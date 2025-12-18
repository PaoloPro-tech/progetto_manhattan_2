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

    # Input domanda/brief (serve per pilotare il RAG in modo corretto)
    user_question: Optional[str]

    # Output degli agenti
    analyst_output: Optional[str]
    internal_research_evidence: Optional[str]  # ✅ chunk grezzi con fonti
    internal_research_output: Optional[str]    # ✅ sintesi citata
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

        # ✅ Usa la domanda reale per fare retrieval (non una query generica)
        user_q = (state.get("user_question") or "").strip()

        # Query ibrida: domanda reale + contesto cliente/settore
        query = (
            f"DOMANDA:\n{user_q}\n\n"
            f"CONTESTO:\nCliente: {state['client_name']}\nSettore: {state['sector']}\n\n"
            "Cerca nei documenti interni informazioni pertinenti alla domanda. "
            "Se la domanda cita un file o un tema specifico, privilegia quel contenuto."
        )

        # Proviamo a recuperare documenti dal vector store
        try:
            docs = self.rag.retrieve(query)

            print(f"      RAG_PERSIST_DIR: {settings.RAG_PERSIST_DIR}")
            print(f"      RAG_COLLECTION_NAME: {settings.RAG_COLLECTION_NAME}")
            print(f"      RAG query: {user_q[:120] + ('...' if len(user_q) > 120 else '')}")
            print(f"      RAG docs retrieved: {len(docs)}")

            if docs:
                evidence = "\n\n".join(
                    [f"[{d.metadata.get('source','unknown')}]\n{d.page_content}" for d in docs]
                )
            else:
                evidence = "NESSUN CONTENUTO RECUPERATO DAL RAG."
        except Exception as e:
            # Gestione “soft”: non blocca il workflow, ma informa nel report
            evidence = (
                "RICERCA INTERNA NON DISPONIBILE.\n"
                f"Dettaglio errore: {str(e)}\n"
                "Suggerimento: assicurati di aver eseguito l'indicizzazione (python -m app.data.rag_index_repo) "
                "e che RAG_PERSIST_DIR punti alla directory corretta."
            )

        # Sintesi “citata” basata SOLO sulle evidenze
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Sei un ricercatore interno. Usa SOLO il contesto fornito (EVIDENZE). "
                "Se non trovi dati nelle evidenze, dillo chiaramente. "
                "Quando usi informazioni, cita SEMPRE la fonte tra [] esattamente come fornita."
            ),
            (
                "user",
                "DOMANDA:\n{q}\n\n"
                "EVIDENZE (con fonti tra []):\n{ev}\n\n"
                "Scrivi una risposta in italiano, chiara e sintetica, con citazioni [] dove appropriato."
            )
        ])

        chain = prompt | self.llm | StrOutputParser()
        out = chain.invoke({"q": user_q or "(nessuna domanda fornita)", "ev": evidence})

        return {
            "internal_research_evidence": evidence,
            "internal_research_output": out
        }

    def researcher_node(self, state: AgentState):
        """Il Ricercatore usa Tavily per cercare news"""
        print(f"   ... 🌍 Ricercatore sta scansionando il web per {state['client_name']} ...")

        query = f"Latest business news and financial trends for {state['client_name']} in {state['sector']} sector"

        try:
            search_results = self.search_tool.invoke(query)
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

        # Passiamo sia evidenze grezze sia sintesi interna
        prompt = ChatPromptTemplate.from_messages([
            ("system", DIRECTOR_SYSTEM_PROMPT),
            ("user", """
CLIENTE: {client}

REPORT ANALISTA (Dati Interni):
{analyst_doc}

EVIDENZE RICERCA INTERNA (Repo RAG - chunk grezzi):
{internal_evidence}

SINTESI RICERCA INTERNA (Repo RAG - citata):
{internal_doc}

REPORT RICERCATORE (News Esterne):
{researcher_doc}
            """)
        ])
        chain = prompt | self.llm | StrOutputParser()

        final_report = chain.invoke({
            "client": state["client_name"],
            "analyst_doc": state.get("analyst_output") or "",
            "internal_evidence": state.get("internal_research_evidence") or "",
            "internal_doc": state.get("internal_research_output") or "",
            "researcher_doc": state.get("researcher_output") or ""
        })

        return {"final_report": final_report}

    # --- 3. Costruzione del Grafo ---
    def build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("analyst", self.analyst_node)
        workflow.add_node("internal_researcher", self.internal_researcher_node)
        workflow.add_node("researcher", self.researcher_node)
        workflow.add_node("director", self.director_node)

        workflow.set_entry_point("analyst")
        workflow.add_edge("analyst", "internal_researcher")
        workflow.add_edge("internal_researcher", "researcher")
        workflow.add_edge("researcher", "director")
        workflow.add_edge("director", END)

        return workflow.compile()

    def run_analysis(self, client: str, sector: str, metrics: dict, user_question: Optional[str] = None):
        app = self.build_graph()

        inputs: AgentState = {
            "client_name": client,
            "sector": sector,
            "financial_metrics": metrics,

            # ✅ domanda/brief che guida il retrieval interno
            "user_question": user_question or "",

            "analyst_output": None,
            "internal_research_evidence": None,
            "internal_research_output": None,
            "researcher_output": None,
            "final_report": None
        }

        return app.invoke(inputs)

    def chat_with_director(self, user_question: str, context_report: str):
        """
        Q&A sul report generato + RAG live.
        In questo modo il Direttore può rispondere anche su dettagli presenti nei documenti interni
        ma non inclusi nel report finale.
        """
        print(f"   ... 💬 Chat in corso: {user_question} ...")

        # ✅ RAG live sulla domanda
        try:
            docs = self.rag.retrieve(user_question)
            if docs:
                rag_evidence = "\n\n".join(
                    [f"[{d.metadata.get('source','unknown')}]\n{d.page_content}" for d in docs]
                )
            else:
                rag_evidence = "NESSUN CONTENUTO RECUPERATO DAL RAG."
        except Exception as e:
            rag_evidence = f"RAG non disponibile: {str(e)}"

        system_prompt = """
Sei il Direttore Strategico.
Regole:
1) Se nelle EVIDENZE INTERNE (RAG) c'è materiale pertinente, usalo come fonte primaria e cita sempre le fonti tra [].
2) Se NON ci sono evidenze interne pertinenti, dillo esplicitamente.
3) Puoi usare il REPORT come contesto, ma non inventare dettagli non presenti in report o evidenze.
Rispondi in italiano, professionale e sintetico.
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user",
             "REPORT (contesto):\n{report}\n\n"
             "EVIDENZE INTERNE (RAG):\n{rag}\n\n"
             "DOMANDA:\n{q}\n")
        ])

        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({"report": context_report, "rag": rag_evidence, "q": user_question})

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

        # ✅ Inserisci una domanda reale per testare l'aggancio del RAG
        outcome = engine.run_analysis(
            "Leonardo",
            "Aerospace",
            mock_metrics,
            user_question="Nel documento interno sui progetti, qual è la timeline e i rischi principali?"
        )

        print("\n=== REPORT FINALE ===")
        print(outcome["final_report"])

        print("\n=== Q&A DIRETTORE (con RAG live) ===")
        ans = engine.chat_with_director(
            "Cosa dice il documento interno X riguardo ai rischi di consegna?",
            outcome["final_report"] or ""
        )
        print(ans)

    except Exception as e:
        print(f"❌ Errore critico: {e}")
