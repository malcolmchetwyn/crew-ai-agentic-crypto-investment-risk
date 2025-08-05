# In src/agents.py

import yaml
from crewai import Agent
from langchain_openai import ChatOpenAI
from crewai_tools import SerperDevTool, ScrapeWebsiteTool, BrowserbaseLoadTool

class CryptoAnalysisAgents:
    def __init__(self):
        # Ensure the path to your agents.yaml is correct
        with open('./src/config/agents.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.7
        )
        self.search_tool = SerperDevTool()
        #self.scrape_tool = ScrapeWebsiteTool()
        #self.browser_tool = BrowserbaseLoadTool() 
        self.browser_tool = BrowserbaseLoadTool(
            content_attrs=['text', 'html_to_markdown']
        )

    def _create_agent(self, name: str) -> Agent:
        agent_config = self.config[name]
        return Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=self.llm,
            verbose=True,
            allow_delegation=True,
            #tools=[self.search_tool, self.scrape_tool]
            tools=[self.search_tool, self.browser_tool]
        )

    def manager_agent(self) -> Agent:
        return self._create_agent('manager')

    def screener_agent(self) -> Agent:
        return self._create_agent('screener')

    def quant_agent(self) -> Agent:
        agent = self._create_agent('quant')
        agent.tools = []
        return agent

    def analyst_agent(self) -> Agent:
        return self._create_agent('analyst')

    def synthesizer_agent(self) -> Agent:
        agent = self._create_agent('synthesizer')
        agent.tools = []
        return agent
        
    # --- ADDED THE MISSING AGENT METHODS HERE ---

    def fact_checker_agent(self) -> Agent:
        """Creates the quantitative fact-checking agent."""
        return self._create_agent('fact_checker')

    def qualitative_verifier_agent(self) -> Agent:
        """Creates the qualitative claim verification agent."""
        return self._create_agent('qualitative_verifier')