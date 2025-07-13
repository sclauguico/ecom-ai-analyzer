# Import libraries
from typing import TypedDict, Dict, Any
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from tool_snowflake import SnowflakeTools
import json
import os
from dotenv import load_dotenv

# Load .env
load_dotenv(override=True)

# Define the structure for storing input query, retrieved data, and AI-generated insights
class AnalysisState(TypedDict):
    query: str
    data: Dict[str, Any]
    analysis: str
    recommendations: str
    next_action: str
    step_count: int
    finished: bool

# Define the EcommerceAgents class: Blueprint for creating the agents and tools
class EcommerceAgents:
    # Define the constructor that runs automatically when an obkect is instantiated from this class
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229", # For the model parameter, define your favorite model as the argument. Mine is Claude Sonnet!
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        # Instantiate supporting objects used by these classes
        self.tools = SnowflakeTools()
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    # Define class methods: Extractor Agent
    def data_extractor_agent(self, state: AnalysisState) -> AnalysisState:
        query_lower = state['query'].lower()
        
        if not state['data']:
            if 'sales' in query_lower or 'revenue' in query_lower:
                state["next_action"] = "get_sales_metrics"
            elif 'product' in query_lower:
                state["next_action"] = "get_top_products"
            else:
                state["next_action"] = "get_sales_metrics"
        elif len(state['data']) == 1:
            if 'product' in query_lower and 'top_products' not in state['data']:
                state["next_action"] = "get_top_products"
            elif 'customer' in query_lower and 'customer_segments' not in state['data']:
                state["next_action"] = "get_customer_segments"
            else:
                state["next_action"] = "analyst_agent"
        else:
            state["next_action"] = "analyst_agent"
        
        state["step_count"] += 1
        return state
    
    # Define class methods: Analyst Agent
    def analyst_agent(self, state: AnalysisState) -> AnalysisState:
        if not state['data']:
            state["next_action"] = "data_extractor_agent"
        else:
            data_str = json.dumps(state["data"], indent=2)
            analyze_prompt = f"""
            Analyze this data for: {state['query']}\nData: {data_str}\n
            Provide 3 clear analysis in bullet points focusing on:
            1. Key metrics and trends
            2. Notable patterns or outliers
            3. Data-driven observations
            
            Keep the analysis factual and specific.
            Make your responses short and concise.
            """
            
            response = self.llm.invoke(analyze_prompt)
            state["analysis"] = response.content
            state["next_action"] = "consultant_agent"
        
        state["step_count"] += 1
        return state
    
    # Define class methods: Consultant Agent
    def consultant_agent(self, state: AnalysisState) -> AnalysisState:
        prompt = f"""
        Based on analysis: {state['analysis']}\n
        
        Provide 3 specific business recommendations in bullet points
        
        Focus on actionable recommendations that can improve:
        - Revenue growth
        - Customer retention
        - Operational efficiency
        
        Be specific and practical. Make your responses short and concise."""
        
        response = self.llm.invoke(prompt)
        state["recommendations"] = response.content
        state["finished"] = True
        state["step_count"] += 1
        return state
    
    # Define class methods: Get sales metrics tool from SnowflakeTools class
    def get_sales_metrics_tool(self, state: AnalysisState) -> AnalysisState:
        result = self.tools.get_sales_metrics()
        state["data"]["sales_metrics"] = result
        return state
    
    # Define class methods: Get top products tool from SnowflakeTools class
    def get_top_products_tool(self, state: AnalysisState) -> AnalysisState:
        result = self.tools.get_top_products()
        state["data"]["top_products"] = result
        return state
    
    # Define class methods: Get customer segments tool from SnowflakeTools class
    def get_customer_segments_tool(self, state: AnalysisState) -> AnalysisState:
        result = self.tools.get_customer_segments()
        state["data"]["customer_segments"] = result
        return state
    
    # Define class methods: router, for directing the flow of the agent system based on the current state object
    # This method returns the name of the next method (or node) to invoke
    # It behaves like a decision controller for the AI agents
    def router(self, state: AnalysisState) -> str:
        if state["finished"] or state["step_count"] >= 10:
            return "end"
        
        action = state.get("next_action", "")
        
        if action == "analyst_agent":
            return "analyst_agent"
        elif action == "consultant_agent":
            return "consultant_agent"
        elif action == "get_sales_metrics":
            return "get_sales_metrics"
        elif action == "get_top_products":
            return "get_top_products"
        elif action == "get_customer_segments":
            return "get_customer_segments"
        else:
            return "data_extractor_agent"
    
    # Define a private method: _build_graph
    # This method constructs and returns the StateGraph object, the control flow
    # for how the AI agents (class methods) interact. The graph is part of this class's internal logic
    # and encapsulates the decision routing between agents.
    def _build_graph(self):
        workflow = StateGraph(AnalysisState)
        
        workflow.add_node("data_extractor_agent", self.data_extractor_agent)
        workflow.add_node("analyst_agent", self.analyst_agent)
        workflow.add_node("consultant_agent", self.consultant_agent)
        workflow.add_node("get_sales_metrics", self.get_sales_metrics_tool)
        workflow.add_node("get_top_products", self.get_top_products_tool)
        workflow.add_node("get_customer_segments", self.get_customer_segments_tool)
        
        # Define the entry point, the first agent to run when the graph is invoked
        workflow.set_entry_point("data_extractor_agent")
        
        # Define conditional transitions based on the router method (a class method used as a controller)
        workflow.add_conditional_edges(
            "data_extractor_agent",
            self.router,
            {
                "get_sales_metrics": "get_sales_metrics",
                "get_top_products": "get_top_products",
                "get_customer_segments": "get_customer_segments",
                "analyst_agent": "analyst_agent",
                "data_extractor_agent": "data_extractor_agent",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "analyst_agent",
            self.router,
            {
                "consultant_agent": "consultant_agent",
                "data_extractor_agent": "data_extractor_agent",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "consultant_agent",
            self.router,
            {
                "end": END
            }
        )
        
        # Add fixed transitions back to the extractor after tool use, loop-like behavior
        workflow.add_edge("get_sales_metrics", "data_extractor_agent")
        workflow.add_edge("get_top_products", "data_extractor_agent")
        workflow.add_edge("get_customer_segments", "data_extractor_agent")
        
        return workflow.compile(checkpointer=self.memory)
    
    # Define the analyze method: this is the public interface (exposed behavior)
    # that users interact with when they want to run a query through the agent system
    def analyze(self, query: str, thread_id: str = "default") -> Dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        
        # Instantiate the initial state object, includes query and default values
        initial_state = AnalysisState(
            query=query,
            data={},
            analysis="",
            recommendations="",
            next_action="",
            step_count=0,
            finished=False
        )
        
        # Invoke the graph (object behavior) using the configured settings and state
        result = self.graph.invoke(initial_state, config=config)
        
        # Return a dictionary of output, a structured response from the AI agents
        return {
            "query": result["query"],
            "total_steps": result["step_count"],
            "data": result["data"],
            "analysis": result["analysis"],
            "recommendations": result["recommendations"]
        }

def test_agents_and_tools():
    # Instantitate agents object from Ecommerce Agent class
    agents = EcommerceAgents()
    # Invoke analyze method
    result = agents.analyze("What are the sales and top products?") # Add the user question as argument for the query parameter
    print(f"Steps: {result['total_steps']}") # Output number of steps taken
    print(f"Data: {list(result['data'].keys())}") # Output result data keys

if __name__ == "__main__":
    test_agents_and_tools()