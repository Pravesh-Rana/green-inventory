# app/data_handler.py
import pandas as pd

products_df = None
customers_df = None
transactions_df = None

def load_data():
    global products_df, customers_df, transactions_df
    try:
        products_df = pd.read_csv('products.csv')
        customers_df = pd.read_csv('customers.csv')
        transactions_df = pd.read_csv('transactions.csv')
        print("--- CSV data loaded into memory successfully. ---")
    except FileNotFoundError:
        print("--- WARNING: CSV data files not found. Sales insights will be unavailable. ---")
    except Exception as e:
        print(f"--- ERROR loading CSV data: {e} ---")

def get_sales_insights_from_cache():
    if transactions_df is None or products_df is None: return "Sales data is not available."
    try:
        sales_data = pd.merge(transactions_df, products_df, on='ProductID')
        top_sellers = sales_data.groupby('ProductName')['Quantity'].sum().nlargest(5).reset_index()
        sales_counts = sales_data['ProductName'].value_counts()
        slow_movers = sales_counts[sales_counts < 5].head(5).reset_index()
        slow_movers.columns = ['ProductName', 'UnitsSold']
        return f"Top Sellers:\n{top_sellers.to_string(index=False)}\n\nSlow Movers:\n{slow_movers.to_string(index=False)}"
    except Exception as e: return f"Error analyzing sales data: {e}"

def get_customer_insights_from_cache():
    if customers_df is None: return "Customer data is not available."
    try:
        age_bins = [18, 30, 45, 60, 100]
        age_labels = ['18-30', '31-45', '46-60', '60+']
        customers_df['AgeGroup'] = pd.cut(customers_df['Age'], bins=age_bins, labels=age_labels, right=False)
        age_distribution = customers_df['AgeGroup'].value_counts().reset_index()
        age_distribution.columns = ['Age_Group', 'Count']
        gender_distribution = customers_df['Gender'].value_counts().reset_index()
        gender_distribution.columns = ['Gender', 'Count']
        return f"Customer Ages:\n{age_distribution.to_string(index=False)}\n\nCustomer Genders:\n{gender_distribution.to_string(index=False)}"
    except Exception as e: return f"Error analyzing customer data: {e}"
