# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField
from .models import ProductType

def product_type_query():
    return ProductType.query

class AddStockForm(FlaskForm):
    product_type = QuerySelectField('Product Type', query_factory=product_type_query, get_label='name', allow_blank=False, validators=[DataRequired()])
    quantity = IntegerField('Quantity to Add', validators=[DataRequired(), NumberRange(min=1)])
    stock_in_date = DateField('Stock-In Date', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Receive Stock & Generate Tags')

class CreateProductTypeForm(FlaskForm):
    name = StringField('Product Name (e.g., 1L Organic Milk)', validators=[DataRequired()])
    default_price = FloatField('Default Price', validators=[DataRequired()])
    submit = SubmitField('Create Product Type')