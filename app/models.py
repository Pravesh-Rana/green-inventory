# app/models.py
from app import db
from datetime import datetime

class ProductType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    default_price = db.Column(db.Float, nullable=False)
    inventory_items = db.relationship('InventoryItem', backref='product_type', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return self.name

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_rfid_tag = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_in_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(120))
    is_sold = db.Column(db.Boolean, default=False)
    sold_date = db.Column(db.DateTime, nullable=True)
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'), nullable=False)

    def __repr__(self):
        return f'<InventoryItem {self.unique_rfid_tag}>'