# app/scheduler.py (Final Corrected Version)

from datetime import date, timedelta
from .models import InventoryItem
import google.generativeai as genai
from flask import current_app
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def get_carbon_footprint_from_gemini(product_name):
    try:
        api_key = current_app.config['GEMINI_API_KEY']
        if not api_key: return None
        genai.configure(api_key=api_key)
        
        # THE FIX IS ON THIS LINE: Use the full, official model name
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"What is the estimated average carbon footprint (in kg of CO2 equivalent) for one unit of '{product_name}'? Provide only the number."
        response = model.generate_content(prompt)
        match = re.search(r'(\d+\.?\d*)', response.text)
        return float(match.group(1)) if match else None
    except Exception: return None

def check_expiring_products(app):
    with app.app_context():
        # ... (The rest of this function is correct and does not need changes)
        sender_email = app.config.get('SENDER_EMAIL')
        store_manager_email = app.config.get('STORE_MANAGER_EMAIL')
        sendgrid_api_key = app.config.get('SENDGRID_API_KEY')
        if not all([sender_email, store_manager_email, sendgrid_api_key]):
            print("--- Email configuration (SendGrid/Recipient) is missing. ---")
            return
        target_date = date.today() + timedelta(days=2)
        expiring_items = InventoryItem.query.filter(InventoryItem.expiry_date == target_date, InventoryItem.is_sold == False).all()
        if not expiring_items:
            print("--- No expiring items to report today. ---")
            return
        print("\n--- Preparing Daily Expiry & Carbon Alert ---")
        expiring_summary = {}
        for item in expiring_items:
            name = item.product_type.name
            if name not in expiring_summary: expiring_summary[name] = {'count': 0}
            expiring_summary[name]['count'] += 1
        email_subject = f"Urgent: Expiry Alert for {target_date.strftime('%B %d, %Y')}"
        email_body_html = "<h1>Daily Green IT Expiry Alert</h1><p>The following items require your immediate attention:</p><hr>"
        for name, data in expiring_summary.items():
            carbon = get_carbon_footprint_from_gemini(name)
            email_body_html += f"<h3>{data['count']}x {name}</h3>"
            if carbon:
                total_carbon = carbon * data['count']
                email_body_html += f"<p style='color:green;'><b>Action:</b> Prioritize selling this batch to prevent a potential waste of <b>{total_carbon:.2f} kg of CO2e</b>.</p>"
            else:
                email_body_html += "<p><b>Action:</b> Prioritize selling this batch to prevent product waste.</p>"
        email_body_html += "<hr><p>This is an automated alert from your Green Inventory Pro system.</p>"
        message = Mail(from_email=sender_email, to_emails=store_manager_email, subject=email_subject, html_content=email_body_html)
        try:
            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)
            print(f"--- Expiry alert email sent successfully! Status Code: {response.status_code} ---")
        except Exception as e:
            print(f"--- FAILED TO SEND EMAIL via SendGrid: {e} ---")
