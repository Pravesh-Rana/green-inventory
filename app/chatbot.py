# app/chatbot.py (Final "Polished & Conversational" Version)

import google.generativeai as genai
from flask import current_app
from .models import InventoryItem, ProductType
from . import db
from datetime import date, timedelta
import pandas as pd
import requests
import json

# --- Tool Functions (remain the same) ---
def search_the_web(query):
    # ... (This function is correct and does not need changes)
    serper_api_key = current_app.config['SERPER_API_KEY']
    if not serper_api_key: return "Error: Serper API key not configured."
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': serper_api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text
    except Exception as e: return f"An error occurred during web search: {e}"

def get_sales_insights():
    # ... (This function is correct and does not need changes)
    try:
        transactions_df = pd.read_csv('transactions.csv')
        products_df = pd.read_csv('products.csv')
        sales_data = pd.merge(transactions_df, products_df, on='ProductID')
        top_sellers = sales_data.groupby('ProductName')['Quantity'].sum().nlargest(5).reset_index()
        sales_counts = sales_data['ProductName'].value_counts()
        slow_movers = sales_counts[sales_counts < 5].head(5).reset_index()
        slow_movers.columns = ['ProductName', 'UnitsSold']
        return f"Top Sellers:\n{top_sellers.to_string(index=False)}\n\nSlow Movers:\n{slow_movers.to_string(index=False)}"
    except Exception: return "Sales data not available."

def get_customer_insights():
    # ... (This function is correct and does not need changes)
    try:
        customers_df = pd.read_csv('customers.csv')
        age_bins = [18, 30, 45, 60, 100]
        age_labels = ['18-30', '31-45', '46-60', '60+']
        customers_df['AgeGroup'] = pd.cut(customers_df['Age'], bins=age_bins, labels=age_labels, right=False)
        age_distribution = customers_df['AgeGroup'].value_counts().reset_index()
        age_distribution.columns = ['Age_Group', 'Count']
        gender_distribution = customers_df['Gender'].value_counts().reset_index()
        gender_distribution.columns = ['Gender', 'Count']
        return f"Customer Ages:\n{age_distribution.to_string(index=False)}\n\nCustomer Genders:\n{gender_distribution.to_string(index=False)}"
    except Exception: return "Customer data not available."

# --- The Main AI Agent Logic ---
def process_query_with_gemini(question):
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key: return "Error: Gemini API key is not configured."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- Data Fetching (remains the same) ---
    try:
        unsold_items = db.session.query(ProductType.name, InventoryItem.expiry_date).join(ProductType).filter(InventoryItem.is_sold == False).all()
        if not unsold_items: inventory_data_string = "The inventory is currently empty."
        else:
            df = pd.DataFrame(unsold_items, columns=['Product_Name', 'Expiry_Date'])
            summary_df = df.groupby(['Product_Name', 'Expiry_Date']).size().reset_index(name='Quantity')
            inventory_data_string = summary_df.to_string(index=False)
    except Exception as e: return f"Error fetching data from the database: {e}"

    # --- The Final, Polished "Master" Prompt ---
    initial_prompt = f"""
    ### YOUR PERSONA ###
    You are 'Green-Ops AI', a friendly, sharp, and helpful business assistant. You are an expert at analyzing data and giving clear, concise, and actionable advice.

    ### YOUR TONE OF VOICE ###
    - **Concise and To the Point:** Get straight to the answer. Use simple bullet points for lists.
    - **Conversational and Natural:** Speak like a helpful colleague, not a formal report.
    - **Proactive:** Always try to add a short, valuable suggestion.

    ### YOUR TOOLS & DATA ###
    1.  **Current Inventory:** What's on the shelves.
    2.  **Sales & Product Performance:** Historical sales data.
    3.  **Customer Demographics:** Information about the customer base.
    4.  **Live Web Search:** For external information.

    ### YOUR LOGIC ###
    1.  Analyze the user's question to understand their goal.
    2.  Synthesize information from your available data to form an expert response.
    3.  If a factual question cannot be answered by the data below, you MUST use the Web Search tool by responding ONLY with a `<tool_code>` block.

    ### --- DATA FOR YOUR ANALYSIS --- ###
    # Current Inventory:
    {inventory_data_string}

    # Sales Performance:
    {get_sales_insights()}

    # Customer Demographics:
    {get_customer_insights()}
    --- END OF DATA ---

    ### EXAMPLES OF YOUR CONCISE STYLE ###
    *   **User Question:** "When will milk expire?"
        *   **Ideal Answer:** "We have 5 cartons of Milk expiring on 2025-07-31. I'd suggest moving them to the front of the shelf to make sure they sell first."
    *   **User Question:** "What promotions can I run?"
        *   **Ideal Answer:** "Based on the data, here are a couple of quick ideas:
            *   We could run a 'Flash Sale' on the Milk since it's expiring soon.
            *   The 'Organic Salad' seems to be a slow mover. Maybe we can try bundling it with a popular item like 'Chicken Breast'?"
    *   **User Question:** "Who is the CEO of Microsoft?"
        *   **Your First Response:** `<tool_code>search_the_web("current CEO of Microsoft")</tool_code>`

    ### YOUR TASK ###
    Begin. Respond to the manager's question using your expert knowledge and concise, conversational style.

    **Manager's Question:** "{question}"
    """

    # --- The ReAct Loop (remains the same) ---
    try:
        response = model.generate_content(initial_prompt)
        if "<tool_code>" in response.text:
            tool_call = response.text.strip()
            query_start = tool_call.find('"') + 1
            query_end = tool_call.rfind('"')
            search_query = tool_call[query_start:query_end]
            print(f"--- AI is searching the web for: '{search_query}' ---")
            search_result = search_the_web(search_query)
            second_prompt = f"{initial_prompt}\n\n<tool_code>search_the_web(\"{search_query}\")</tool_code>\n\n<observation>\n{search_result}\n</observation>\n\nNow, use the observation to provide a final, conversational answer."
            final_response = model.generate_content(second_prompt)
            return final_response.text
        else:
            return response.text
    except Exception as e:
        return f"An error occurred in the AI agent loop: {e}"