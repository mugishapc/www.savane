from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Reduced to 200 characters

    # Relationships (back_populates)
    income_expenses = db.relationship('IncomeExpense', back_populates='user', lazy=True)
    sales = db.relationship('Sale', back_populates='user', lazy=True)
    stocks = db.relationship('Stock', back_populates='user', lazy=True)

    def set_password(self, password):
        # Use pbkdf2:sha256 instead of scrypt for shorter hash length
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class IncomeExpense(db.Model):
    __tablename__ = 'income_expenses'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='income_expenses')


class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    product = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='sales')


class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    product = db.Column(db.String(100), nullable=False)
    quantity_in = db.Column(db.Integer, default=0)
    quantity_out = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='stocks')