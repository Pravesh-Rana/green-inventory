# app/routes.py

from flask import render_template, flash, redirect, url_for, request, jsonify, Blueprint, Response
from app import db
from .models import ProductType, InventoryItem
from .forms import AddStockForm, CreateProductTypeForm
from datetime import date, timedelta, datetime
import time
import pandas as pd
from io import StringIO
from .chatbot import process_query_with_gemini
from .scheduler import get_carbon_footprint_from_gemini

bp = Blueprint('main', __name__)

# --- (Dashboard, Manage Products, Delete, Add Stock, Sales Terminal routes are unchanged) ---
@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    # ... (code is correct)
    expiring_items = InventoryItem.query.filter(InventoryItem.expiry_date <= date.today() + timedelta(days=2), InventoryItem.expiry_date >= date.today(), InventoryItem.is_sold == False).all()
    expiring_summary = {}
    for item in expiring_items:
        product_name = item.product_type.name
        if product_name not in expiring_summary:
            expiring_summary[product_name] = {'count': 0, 'location': item.location, 'expiry': item.expiry_date, 'carbon': 0}
        expiring_summary[product_name]['count'] += 1
    for name, data in expiring_summary.items():
        carbon_per_item = get_carbon_footprint_from_gemini(name)
        if carbon_per_item: data['carbon'] = carbon_per_item * data['count']
    total_items = InventoryItem.query.filter_by(is_sold=False).count()
    total_value = db.session.query(db.func.sum(InventoryItem.price)).filter_by(is_sold=False).scalar() or 0
    return render_template('index.html', title='Dashboard', expiring_summary=expiring_summary, total_items=total_items, total_value=total_value)

# --- NEW ROUTE for the Power BI Dashboard ---
@bp.route('/analytics_dashboard')
def analytics_dashboard():
    return render_template('analytics_dashboard.html', title='Analytics Dashboard')

@bp.route('/manage_products', methods=['GET', 'POST'])
def manage_products():
    # ... (code is correct)
    form = CreateProductTypeForm()
    if form.validate_on_submit():
        product_name = form.name.data.strip().title()
        existing_product = ProductType.query.filter_by(name=product_name).first()
        if existing_product:
            flash(f'Error: Product Type "{product_name}" already exists.', 'danger')
        else:
            new_product_type = ProductType(name=product_name, default_price=form.default_price.data)
            db.session.add(new_product_type)
            db.session.commit()
            flash(f'Product Type "{product_name}" created!', 'success')
        return redirect(url_for('main.manage_products'))
    products = ProductType.query.order_by(ProductType.id).all()
    return render_template('manage_products.html', title="Manage Product Types", products=products, form=form)

@bp.route('/delete_product_type/<int:product_type_id>', methods=['POST'])
def delete_product_type(product_type_id):
    # ... (code is correct)
    product_to_delete = ProductType.query.get_or_404(product_type_id)
    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        flash(f'Product Type "{product_to_delete.name}" and all its inventory have been successfully deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the product: {e}', 'danger')
    return redirect(url_for('main.manage_products'))

@bp.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    # ... (code is correct)
    form = AddStockForm()
    if form.validate_on_submit():
        product_type = form.product_type.data
        for i in range(form.quantity.data):
            unique_tag = f"{product_type.id}-{int(time.time())}-{i+1}"
            new_item = InventoryItem(unique_rfid_tag=unique_tag, price=product_type.default_price, stock_in_date=form.stock_in_date.data, expiry_date=form.expiry_date.data, location=form.location.data, product_type_id=product_type.id)
            db.session.add(new_item)
        db.session.commit()
        flash(f'{form.quantity.data} items for "{product_type.name}" have been added.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_stock.html', title='Receive Stock', form=form)

@bp.route('/sales_terminal', methods=['GET', 'POST'])
def sales_terminal():
    # ... (code is correct)
    if request.method == 'POST':
        rfid_tag = request.form.get('rfid_tag', '').strip()
        if not rfid_tag:
            flash('Please enter an RFID Tag.', 'danger')
            return redirect(url_for('main.sales_terminal'))
        item = InventoryItem.query.filter_by(unique_rfid_tag=rfid_tag).first()
        if not item:
            flash(f'Error: RFID Tag "{rfid_tag}" not found.', 'danger')
        elif item.is_sold:
            flash(f'Warning: Item with tag "{rfid_tag}" was already sold.', 'warning')
        else:
            item.is_sold = True
            item.sold_date = datetime.utcnow()
            db.session.commit()
            flash(f'Success: Sold "{item.product_type.name}" (Tag: {rfid_tag})', 'success')
        return redirect(url_for('main.sales_terminal'))
    return render_template('sales_terminal.html', title='Sales Terminal')

# --- NEW FUNCTION TO DISPLAY ALL INVENTORY ---
@bp.route('/full_inventory')
def full_inventory():
    # Query all items, join with their product type, and order them
    # This puts all the "In Stock" items at the top
    items = InventoryItem.query.join(ProductType).order_by(InventoryItem.is_sold, ProductType.name, InventoryItem.expiry_date).all()
    return render_template('full_inventory.html', title='Full Inventory List', items=items)

# --- (Download and Chatbot routes are unchanged) ---
@bp.route('/download_inventory')
def download_inventory():
    # ... (code is correct)
    items_in_stock = db.session.query(InventoryItem.unique_rfid_tag, ProductType.name, InventoryItem.price, InventoryItem.stock_in_date, InventoryItem.expiry_date, InventoryItem.location).join(ProductType).filter(InventoryItem.is_sold == False).order_by(ProductType.name, InventoryItem.expiry_date).all()
    df = pd.DataFrame(items_in_stock, columns=['RFID_Tag', 'Product_Name', 'Price', 'Stock_In_Date', 'Expiry_Date', 'Location'])
    csv_output = StringIO()
    df.to_csv(csv_output, index=False)
    csv_output.seek(0)
    return Response(csv_output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=inventory_report.csv"})

@bp.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    # ... (code is correct)
    data = request.get_json()
    question = data.get('question')
    response = process_query_with_gemini(question)
    return jsonify({'answer': response})