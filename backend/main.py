# Import libraries
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # BaseModel is a superclass for defining data models
from langgraph_agents import EcommerceAgents # Self-defined / custom class from langgraph_agents.py
from tool_snowflake import SnowflakeTools # Self-defined / custom class from tool_snowflake.py
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Instantiate the FastAPI application class to create FastAPI object app
app = FastAPI(title="E-Commerce AI Agents Analyzer API")

# Add middleware to the app using a method of the app instance
app.add_middleware(
    CORSMiddleware, # Class used to handle cross-origin requests
    allow_origins=["http://localhost:3000"], # Parameters passed to the constructor and arguments (actual values) added to parameters
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate classes to create objects
agents = EcommerceAgents() # Constructor of EcommerceAgents is invoked
tools = SnowflakeTools() # Constructor of SnowflakeTools is invoked
executor = ThreadPoolExecutor(max_workers=4) # ThreadPoolExecutor object instantiated

# Define a data model using class which inherits from Pydantic's BaseModel
class AnalysisRequest(BaseModel):
    query: str # Attribute (parameter) of the class

# Another data model class used for response formatting
class QuickInsight(BaseModel):
    metric: str # Class parameters
    value: str
    trend: str

# Define a method which is an asynchronous function to check API health
# Decorator: @app.get registers this method to respond to HTTP GET requests at "/health"
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ecommerce-ai-agents-analyzer"}

# Define another method for the /quick-insights endpoint
# Decorator: @app.get binds this method to a route for GET requests
@app.get("/quick-insights")
async def get_quick_insights():
    def get_insights(): # Inner function, used in executor thread
        # Method invocations on the 'tools' object
        sales = tools.get_sales_metrics(30)
        products = tools.get_top_products(3)
        segments = tools.get_customer_segments()
        
        # Return list of instantiated QuickInsight objects which are passing arguments to constructor
        return [
            QuickInsight(
                metric="Total Revenue (30 days)",
                value=f"${sales['total_revenue']:,.2f}",
                trend=f"{sales['total_orders']} orders"
            ),
            QuickInsight(
                metric="Top Product",
                value=products['top_products'][0]['product_name'] if products['top_products'] else "N/A",
                trend=f"${products['top_products'][0]['total_revenue']:,.2f}" if products['top_products'] else "N/A"
            ),
            QuickInsight(
                metric="Active Customers",
                value=str(sum(seg['customer_count'] for seg in segments['customer_segments'])),
                trend="Across all segments"
            )
        ]
    
    # Use asyncio to run blocking function in a separate thread using event loop
    loop = asyncio.get_event_loop()
    insights = await loop.run_in_executor(executor, get_insights)
    return {"insights": insights}

# Define a method that handles POST requests and accepts a class instance as a parameter
# Decorator: @app.post binds this method to HTTP POST requests at the "/analyze" route
@app.post("/analyze")
async def analyze_data(request: AnalysisRequest): # Method takes in a parameter of type AnalysisRequest
    def run_analysis(): # Inner function (non-async) to run in thread
        return agents.analyze(request.query) # Method call on the 'agents' class instance
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_analysis)
    
    # Structured response, includes data returned from the analyze method
    return {
        "analysis_id": "temp_id",
        "query": result["query"],
        "status": "completed",
        "results": {
            "total_steps": result["total_steps"],
            "data": result["data"],
            "analysis": result["analysis"],
            "recommendations": result["recommendations"]
        }
    }

# Main entry point of the script when executed directly
if __name__ == "__main__":
    print("Starting E-Commerce AI Agents Analyzer API...")
    # Start the web server: method call that runs the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)