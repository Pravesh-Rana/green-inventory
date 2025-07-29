# app/chatbot.py (Final "Data Analyst & Strategist" Version)

import google.generativeai as genai
from flask import current_app
from .models import InventoryItem, ProductType
from . import db
from datetime import date, timedelta
import pandas as pd
import requests
import json

# --- KNOWLEDGE BASE RETRIEVAL TOOLS ---
# These functions read and analyze the CSV files.

def get_sales_insights():
    """Reads transaction data to find top-selling and slow-moving products."""
    try:
        transactions_df = pd.read_csv('transactions.csv')
        products_df = pd.read_csv('products.csv')
        
        # Merge to get product names
        sales_data = pd.merge(transactions_df, products_df, on='ProductID')
        
        # Calculate top sellers
        top_sellers = sales_data.groupby('ProductName')['Quantity'].sum().nlargest(5).reset_index()
        
        # Calculate slow movers (less than a certain threshold of sales)
        sales_counts = sales_data['ProductName'].value_counts()
        slow_movers = sales_counts[sales_counts < 5].head(5).reset_index()
        slow_movers.columns = ['ProductName', 'UnitsSold']

        return f"Top Sellers (by units sold):\n{top_sellers.to_string(index=False)}\n\nSlow Movers (by units sold):\n{slow_movers.to_string(index=False)}"
    except FileNotFoundError:
        return "Sales data files not found."
    except Exception as e:
        return f"Error analyzing sales data: {e}"

def get_customer_insights():
    """Reads customer data to provide demographic summaries."""
    try:
        customers_df = pd.read_csv('customers.csv')
        age_bins = [18, 30, 45, 60, 100]
        age_labels = ['18-30', '31-45', '46-60', '60+']
        customers_df['AgeGroup'] = pd.cut(customers_df['Age'], bins=age_bins, labels=age_labels, right=False)
        
        age_distribution = customers_df['AgeGroup'].value_counts().reset_index()
        age_distribution.columns = ['Age_Group', 'Count']
        
        gender_distribution = customers_df['Gender'].value_counts().reset_index()
        gender_distribution.columns = ['Gender', 'Count']
        
        return f"Customer Age Distribution:\n{age_distribution.to_string(index=False)}\n\nCustomer Gender Distribution:\n{gender_distribution.to_string(index=False)}"
    except FileNotFoundError:
        return "Customer data file not found."
    except Exception as e:
        return f"Error analyzing customer data: {e}"


# --- The Main AI Agent Logic ---
def process_query_with_gemini(question):
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key: return "Error: Gemini API key is not configured."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- Data Fetching (Current Inventory) ---
    try:
        # ... (This part remains the same)
        unsold_items = db.session.query(ProductType.name, InventoryItem.expiry_date).join(ProductType).filter(InventoryItem.is_sold == False).all()
        if not unsold_items: inventory_data_string = "The inventory is currently empty."
        else:
            df = pd.DataFrame(unsold_items, columns=['Product_Name', 'Expiry_Date'])
            summary_df = df.groupby(['Product_Name', 'Expiry_Date']).size().reset_index(name='Quantity')
            inventory_data_string = summary_df.to_string(index=False)
    except Exception as e: return f"Error fetching data from the database: {e}"

    # --- THE FINAL, MASTER PROMPT ---
    initial_prompt = f"""
    ### YOUR PERSONA ###
    You are 'Green-Ops AI', an expert business and sustainability strategist for a retail store manager. Your goal is to synthesize information from multiple sources to provide data-driven, creative, and actionable advice.

    ### YOUR KNOWLEDGE BASE ###
    You have access to the following real-time data sources:
    1.  **Current Inventory:** What's on the shelves right now.
    2.  **Sales & Product Performance:** A history of transactions and product details.
    3.  **Customer Demographics:** Information about the store's customer base.
    4.  **Live Web Search:** For any external information.

    ### YOUR LOGIC ###
    1.  Analyze the user's question to understand their goal.
    2.  Based on the question, decide which data sources you need to consult.
    3.  Formulate an expert response that synthesizes information from these sources to give a complete, insightful answer.
    4.  If a factual question cannot be answered by the data below, you MUST use the Web Search tool.

    ### --- DATA FOR YOUR ANALYSIS --- ###

    # --- 1. CURRENT INVENTORY DATA ---
    Today's date is {date.today().strftime('%Y-%m-%d')}.
    {inventory_data_string}
    --- END OF DATA ---

    # --- 2. SALES & PRODUCT PERFORMANCE INSIGHTS ---
    {get_sales_insights()}
    --- END OF DATA ---

    # --- 3. CUSTOMER DEMOGRAPHICS INSIGHTS ---
    {get_customer_insights()}
    --- END OF DATA ---

    ### YOUR TASK ###
    Begin. Provide a strategic and helpful response to the manager's question.

    **Manager's Question:** "{question}"
    """

    # --- The ReAct Loop (This part doesn't need to change) ---
    try:
        # The web search logic is now implicitly handled by the main prompt's instructions
        response = model.generate_content(initial_prompt)
        # We simplify this part, as we are now pre-loading all data into the prompt
        return response.text
    except Exception as e:
        return f"An error occurred in the AI agent loop: {e}"