from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, NumberRange, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    department = SelectField('Department', choices=[
        ('accounting', 'Accounting'),
        ('commercial', 'Commercial'),
        ('stock', 'Stock'),
        ('finance', 'Finance'),
        ('management', 'Management')
    ], validators=[DataRequired()])
    submit = SubmitField('Register')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    department = SelectField('Department', choices=[
        ('accounting', 'Accounting'),
        ('commercial', 'Commercial'),
        ('stock', 'Stock'),
        ('finance', 'Finance'),
        ('management', 'Management')
    ], validators=[DataRequired()])
    submit = SubmitField('Update User')

class IncomeExpenseForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    type = SelectField('Type', choices=[('income', 'Income'), ('expense', 'Expense')], validators=[DataRequired()])
    submit = SubmitField('Record')

class SaleForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    product = StringField('Product Name', validators=[DataRequired()])  # Added product field
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Record Sale')

class StockForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    product = StringField('Product', validators=[DataRequired()])
    quantity_in = IntegerField('Quantity In', default=0, validators=[NumberRange(min=0)])
    quantity_out = IntegerField('Quantity Out', default=0, validators=[NumberRange(min=0)])
    submit = SubmitField('Record Stock Movement')