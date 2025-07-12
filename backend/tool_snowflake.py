# Import libraries
import json
import pandas as pd
import snowflake.connector
from datetime import datetime, timedelta
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load .env
load_dotenv(override=True)

# Define SnowflakeTools
class SnowflakeTools:
    def __init__(self):
        self.conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_RAW_SCHEMA'),
            role=os.getenv('SNOWFLAKE_ROLE'),
            insecure_mode=True,
        )
    
    # Function for getting the sales metrics
    def get_sales_metrics(self, days: int = 30) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM orders 
        WHERE order_date >= %s AND order_date <= %s
        """
        
        cursor.execute(query, (start_date, end_date))
        result = cursor.fetchone()
        
        return {
            "period_days": days,
            "total_orders": result[0] or 0,
            "total_revenue": float(result[1] or 0),
            "avg_order_value": float(result[2] or 0),
            "unique_customers": result[3] or 0
        }
    
    # Function for getting the top products
    def get_top_products(self, no_products: int = 10) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            p.product_name,
            SUM(oi.quantity) as total_sold,
            SUM(oi.total_price) as total_revenue,
            COUNT(DISTINCT oi.order_id) as orders_count
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_revenue DESC
        LIMIT %s
        """
        
        cursor.execute(query, (no_products,))
        results = cursor.fetchall()
        
        products = []
        for row in results:
            products.append({
                "product_name": row[0],
                "total_sold": row[1],
                "total_revenue": float(row[2]),
                "orders_count": row[3]
            })
        
        return {"top_products": products}
    
    # Function for defining customer segments (simple example based on income)
    def get_customer_segments(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            CASE 
                WHEN annual_income >= 80000 THEN 'High Value'
                WHEN annual_income >= 50000 THEN 'Mid Value'
                ELSE 'Low Value'
            END as segment,
            COUNT(*) as customer_count,
            AVG(annual_income) as avg_income
        FROM customers
        WHERE is_active = TRUE
        GROUP BY segment
        ORDER BY avg_income DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        segments = []
        for row in results:
            segments.append({
                "segment": row[0],
                "customer_count": row[1],
                "avg_income": float(row[2])
            })
        
        return {"customer_segments": segments}

# Function for testing SnowflakeTools class and its functions
def test_tools():
    tools = SnowflakeTools()
    
    print("Testing sales metrics:")
    sales = tools.get_sales_metrics(30) # Set days parameter and pass in any number as argument, setting 30 for this project limit
    print(json.dumps(sales, indent=2))
    
    print("\nTesting top products:")
    products = tools.get_top_products(5) # Set no_products parameter and pass in any number as argument, setting 10 for this project limit
    print(json.dumps(products, indent=2))
    
    print("\nTesting customer segments:")
    segments = tools.get_customer_segments()
    print(json.dumps(segments, indent=2))

if __name__ == "__main__":
    # Run test_tools
    test_tools()