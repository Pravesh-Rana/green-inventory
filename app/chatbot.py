# app/chatbot.py (Final "Advanced AI Agent" Version)

import google.generativeai as genai
from flask import current_app
from .models import InventoryItem, ProductType
from . import db
from datetime import date, timedelta
import pandas as pd
import requests
import json

# --- Tool 1: Web Search Function ---
def search_the_web(query):
    """
    This function acts as our live web search tool.
    It takes a search query, calls the Serper API, and returns the results.
    """
    serper_api_key = current_app.config['SERPER_API_KEY']
    if not serper_api_key:
        return "Error: Serper API key not configured."

    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text
    except Exception as e:
        return f"An error occurred during web search: {e}"

# --- The Main AI Agent Logic ---
def process_query_with_gemini(question):
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key: return "Error: Gemini API key is not configured."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- Data Fetching ---
    try:
        unsold_items = db.session.query(ProductType.name, InventoryItem.expiry_date, InventoryItem.location).join(ProductType).filter(InventoryItem.is_sold == False).all()
        if not unsold_items:
            data_string = "The inventory is currently empty."
        else:
            df = pd.DataFrame(unsold_items, columns=['Product_Name', 'Expiry_Date', 'Location'])
            summary_df = df.groupby(['Product_Name', 'Expiry_Date', 'Location']).size().reset_index(name='Quantity')
            data_string = summary_df.to_string(index=False)
    except Exception as e: return f"Error fetching data from the database: {e}"

    # --- The New, Highly-Trained AI Prompt ---
    initial_prompt = f"""
    ### YOUR PERSONA ###
    You are 'Green-Ops AI', an elite sustainability and operations analyst for a retail store manager. Your goal is to provide accurate data, insightful analysis, and actionable advice.

    ### YOUR TOOLS ###
    1.  **Inventory Database:** A real-time list of products currently in stock.
    2.  **Web Search:** A tool to get up-to-the-minute information on any topic.

    ### YOUR CORE LOGIC (Process in this order) ###
    1.  **Analyze the question's intent.**
    2.  **Is it about the store's current inventory?** (e.g., "how many," "what's in stock," "where is," product names from the data). If YES, answer ONLY using the `INVENTORY DATA` provided below.
    3.  **Is it a factual question about the world?** (e.g., "who is," "what is," "latest news," "carbon footprint of..."). If YES, you MUST use the `Web Search` tool to ensure your answer is accurate and up-to-date. To do this, respond ONLY with a `<tool_code>` block.
    4.  **Is it a request for ideas or general conversation?** If YES, answer from your own general knowledge.

    ### YOUR AVAILABLE DATA ###
    --- INVENTORY DATA ---
    Today's date is {date.today().strftime('%Y-%m-%d')}.
    {data_string}
    --- END OF DATA ---

    ### EXAMPLES OF HIGH-QUALITY RESPONSES ###
    *   **Inventory Question:** "How many cartons of milk do we have?"
        *   **Ideal Answer:** "We currently have 10 cartons of Milk in stock. **Suggestion:** Since this is a popular item, you might consider checking the stock again tomorrow to see if a new order is needed."
    *   **Web Search Question:** "What is the latest news on plastic-free packaging?"
        *   **Your First Response:** `<tool_code>search_the_web("latest news on plastic-free packaging alternatives for retail")</tool_code>`
    *   **Environmental Impact Question:** "Is beef bad for the environment?"
        *   **Ideal Answer:** "Yes, from a sustainability perspective, beef production has a significantly higher carbon and water footprint compared to other proteins. A typical estimate is around 60-100 kg of CO2e per kg of beef. **Suggestion:** Promoting chicken or plant-based alternatives can be a great way to offer customers more sustainable options."

    ### YOUR TASK ###
    Begin. Analyze the manager's question and respond according to your rules.

    **Manager's Question:** "{question}"
    """

    # --- The ReAct (Reason + Act) Loop ---
    try:
        # First call to the AI
        response = model.generate_content(initial_prompt)
        
        # Check if the AI wants to use our search tool
        if "<tool_code>" in response.text:
            tool_call = response.text.strip()
            # Extract the search query from the AI's response
            query_start = tool_call.find('"') + 1
            query_end = tool_call.rfind('"')
            search_query = tool_call[query_start:query_end]

            # Execute the search tool
            print(f"--- AI is searching the web for: '{search_query}' ---")
            search_result = search_the_web(search_query)

            # Create a new prompt including the search results (the "observation")
            second_prompt = f"{initial_prompt}\n\n<tool_code>search_the_web(\"{search_query}\")</tool_code>\n\n<observation>\n{search_result}\n</observation>\n\nNow, use the observation from your web search to provide a final, conversational answer."
            
            # Second call to the AI to get the final answer
            final_response = model.generate_content(second_prompt)
            return final_response.text
        else:
            # If no tool was needed, the first response is the final answer
            return response.text
    except Exception as e:
        return f"An error occurred in the AI agent loop: {e}"