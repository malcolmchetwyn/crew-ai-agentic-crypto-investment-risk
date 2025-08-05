# In src/crew.py

from crewai import Crew, Process
from langchain_openai import ChatOpenAI
from .agents import CryptoAnalysisAgents
from .tasks import CryptoAnalysisTasks

class HierarchicalAnalysisCrew:
    def __init__(self, crypto_symbol: str):
        self.crypto_symbol = crypto_symbol
        self.agents = CryptoAnalysisAgents()
        self.tasks = CryptoAnalysisTasks()

    def run(self):
        # Instantiate all agents
        manager = self.agents.manager_agent() # --- RE-ADDED ---
        screener = self.agents.screener_agent()
        fact_checker = self.agents.fact_checker_agent()
        quant = self.agents.quant_agent()
        analyst = self.agents.analyst_agent()
        qualitative_verifier = self.agents.qualitative_verifier_agent()
        synthesizer = self.agents.synthesizer_agent()

        # Instantiate all tasks
        task_screener = self.tasks.screener_task(screener, self.crypto_symbol)
        task_fact_checker = self.tasks.fact_checker_task(fact_checker, context=[task_screener])
        task_quant = self.tasks.quant_task(quant, self.crypto_symbol, context=[task_fact_checker])
        task_analyst = self.tasks.analyst_task(analyst, self.crypto_symbol, context=[task_quant])
        task_qualitative_verifier = self.tasks.qualitative_verification_task(qualitative_verifier, context=[task_analyst])
        task_synthesizer = self.tasks.synthesizer_task(
            synthesizer,
            self.crypto_symbol,
            context=[task_fact_checker, task_quant, task_analyst, task_qualitative_verifier]
        )

        # Assemble the crew with the hierarchical process
        crew = Crew(
            agents=[
                manager, 
                screener, 
                fact_checker, 
                quant, 
                analyst, 
                qualitative_verifier,
                synthesizer
            ],
            tasks=[
                task_screener, 
                task_fact_checker, 
                task_quant, 
                task_analyst, 
                task_qualitative_verifier,
                task_synthesizer
            ],
            process=Process.hierarchical,  # --- CHANGED BACK ---
            manager_llm=ChatOpenAI(model="gpt-4.1-mini"), # --- RE-ADDED ---
            verbose=True
        )

        result = crew.kickoff()
        return result