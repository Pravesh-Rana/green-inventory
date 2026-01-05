# app/chatbot.py (Final Corrected Version)

import google.generativeai as genai
from flask import current_app
from .models import InventoryItem, ProductType
from . import db
from datetime import date
import pandas as pd
import requests
import json
from .data_handler import get_sales_insights_from_cache, get_customer_insights_from_cache

# --- Tool 1: Web Search Function (remains the same) ---
def search_the_web(query):
    # ... (code is unchanged)
    serper_api_key = current_app.config['SERPER_API_KEY']
    if not serper_api_key: return "Error: Serper API key not configured."
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': serper_api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text
    except Exception as e: return f"An error occurred during web search: {e}"

# --- The Main AI Agent Logic (UPDATED) ---
def process_query_with_gemini(question):
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key: return "Error: Gemini API key is not configured."
    genai.configure(api_key=api_key)
    
    # THE FIX IS HERE: Use the universal 'gemini-pro' model
    model = genai.GenerativeModel('gemini-pro')

    # --- Data Fetching (remains the same) ---
    try:
        unsold_items = db.session.query(ProductType.name, InventoryItem.expiry_date).join(ProductType).filter(InventoryItem.is_sold == False).all()
        if not unsold_items: inventory_data_string = "The inventory is currently empty."
        else:
            df = pd.DataFrame(unsold_items, columns=['Product_Name', 'Expiry_Date'])
            summary_df = df.groupby(['Product_Name', 'Expiry_Date']).size().reset_index(name='Quantity')
            inventory_data_string = summary_df.to_string(index=False)
    except Exception as e: return f"Error fetching data from the database: {e}"

    # --- The Final, Polished "Master" Prompt (remains the same) ---
    initial_prompt = f"""
    ### YOUR PERSONA ###
    You are 'Green-Ops AI', a friendly, sharp, and helpful business assistant.
    # ... (rest of the prompt is unchanged)
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
