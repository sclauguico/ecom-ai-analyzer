from IPython.display import Image, display
from langgraph_agents import EcommerceAgents
import os

def show_graph():
    agents = EcommerceAgents()
    display(Image(agents.graph.get_graph().draw_mermaid_png()))

def save_graph(filename="workflow.png"):
    agents = EcommerceAgents()
    png_data = agents.graph.get_graph().draw_mermaid_png()
    
    # Get current working directory
    current_dir = os.getcwd()
    full_path = os.path.join(current_dir, filename)
    
    with open(full_path, 'wb') as f:
        f.write(png_data)
    
    print(f"Saved to: {full_path}")
    
    # Open file explorer to the location
    os.startfile(current_dir)

if __name__ == "__main__":
    save_graph()