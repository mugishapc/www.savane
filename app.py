from flask import Flask, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, IncomeExpense, Sale, Stock
from forms import LoginForm, RegistrationForm, IncomeExpenseForm, SaleForm, StockForm, EditUserForm
from datetime import datetime, timedelta
import os
import pdfkit
from io import BytesIO
from weasyprint import HTML

app = Flask(__name__)
app.config['SECRET_KEY'] = 'd29c234ca310aa6990092d4b6cd4c4854585c51e1f73bf4de510adca03f5bc4e'  

import os

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_name = os.environ.get("DB_NAME")
db_port = os.environ.get("DB_PORT", "17954")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "ssl": {"ssl_mode": "REQUIRED"}
    }
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_tables():
    with app.app_context():
        # First drop all tables to ensure clean schema
        db.drop_all()
        db.create_all()
        
        # Create default admin user if no users exist
        if not User.query.first():
            admin = User(
                username='administrator', 
                full_name='Management',
                department='DIRECTEUR GENERAL',
                role='management'
            )
            admin.set_password('0220Osias#')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created successfully!")

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role
    
    if role == 'accounting':
        return redirect(url_for('accounting_dashboard'))
    elif role == 'commercial':
        return redirect(url_for('commercial_dashboard'))
    elif role == 'stock':
        return redirect(url_for('stock_dashboard'))
    elif role == 'finance':
        return redirect(url_for('finance_dashboard'))
    elif role == 'management':
        return redirect(url_for('management_dashboard'))
    else:
        return render_template('unauthorized.html')

# Add user management route for management role
@app.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'management':
        return render_template('unauthorized.html')
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

# Add route for creating new users (admin only)
@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role != 'management':
        return render_template('unauthorized.html')
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('create_user.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            full_name=form.full_name.data,
            department=form.department.data,
            role=form.department.data  # Role matches department for simplicity
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('User created successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('create_user.html', form=form)

# Add user deletion route
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'management':
        return render_template('unauthorized.html')
    
    user_to_delete = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user_to_delete.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('manage_users'))
    
    # Prevent deletion of the default admin account
    if user_to_delete.username == 'administrator':
        flash('Cannot delete the default administrator account.', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        # Delete all related records first
        IncomeExpense.query.filter_by(user_id=user_id).delete()
        Sale.query.filter_by(user_id=user_id).delete()
        Stock.query.filter_by(user_id=user_id).delete()
        
        # Now delete the user
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('manage_users'))

# Add route for editing users (admin only)
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'management':
        return render_template('unauthorized.html')
    
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    if form.validate_on_submit():
        # Update user details
        user.username = form.username.data
        user.full_name = form.full_name.data
        user.department = form.department.data
        user.role = form.department.data  # Role matches department
        
        # Update password if provided
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('edit_user.html', form=form, user=user)

# Add route for downloading PDF report (admin only)
@app.route('/download_report')
@login_required
def download_report():
    if current_user.role != 'management':
        return render_template('unauthorized.html')
    
    # Calculate date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Get data for the report
    income_expenses = IncomeExpense.query.filter(
        IncomeExpense.date >= start_date,
        IncomeExpense.date <= end_date
    ).all()
    
    sales = Sale.query.filter(
        Sale.date >= start_date,
        Sale.date <= end_date
    ).all()
    
    stock_movements = Stock.query.filter(
        Stock.date >= start_date,
        Stock.date <= end_date
    ).all()
    
    # Calculate totals
    total_income = sum(r.amount for r in income_expenses if r.type == 'income')
    total_expense = sum(r.amount for r in income_expenses if r.type == 'expense')
    balance = total_income - total_expense
    total_sales = sum(sale.total for sale in sales)
    
    # Render HTML template
    html = render_template(
        'report_template.html',
        start_date=start_date,
        end_date=end_date,
        income_expenses=income_expenses,
        sales=sales,
        stock_movements=stock_movements,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        total_sales=total_sales,
        now=datetime.now()  # Pass current datetime to template
    )
    
    try:
        # Generate PDF using weasyprint
        pdf = HTML(string=html).write_pdf()
        
        # Create a BytesIO object to store the PDF
        pdf_buffer = BytesIO()
        pdf_buffer.write(pdf)
        pdf_buffer.seek(0)
        
        # Send the PDF as a response
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'savane_report_{end_date.strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('management_dashboard'))

@app.route('/dashboard/accounting', methods=['GET', 'POST'])
@login_required
def accounting_dashboard():
    if current_user.role != 'accounting':
        return render_template('unauthorized.html')
    
    form = IncomeExpenseForm()
    if form.validate_on_submit():
        try:
            record = IncomeExpense(
                date=datetime.combine(form.date.data, datetime.min.time()),
                description=form.description.data,
                amount=form.amount.data,
                type=form.type.data,
                user_id=current_user.id
            )
            db.session.add(record)
            db.session.commit()
            flash('Record added successfully!', 'success')
            return redirect(url_for('accounting_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding record: {str(e)}', 'danger')
    
    # Get records and format them for display
    records = IncomeExpense.query.order_by(IncomeExpense.date.desc()).all()
    simplified_records = []
    
    for record in records:
        income = record.amount if record.type == 'income' else None
        expense = record.amount if record.type == 'expense' else None
        
        simplified_records.append({
            'date': record.date.strftime('%Y-%m-%d'),
            'income': income,
            'expense': expense
        })
    
    return render_template('dashboard_accounting.html', form=form, records=simplified_records)

@app.route('/dashboard/commercial', methods=['GET', 'POST'])
@login_required
def commercial_dashboard():
    if current_user.role != 'commercial':
        return render_template('unauthorized.html')
    
    form = SaleForm()
    if form.validate_on_submit():
        total = form.quantity.data * form.unit_price.data
        sale = Sale(
            date=datetime.combine(form.date.data, datetime.min.time()),
            product=form.product.data,  # Added product field
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            total=total,
            user_id=current_user.id
        )
        db.session.add(sale)
        db.session.commit()
        flash('Sale recorded successfully!', 'success')
        return redirect(url_for('commercial_dashboard'))
    
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return render_template('dashboard_commercial.html', form=form, sales=sales)

@app.route('/dashboard/stock', methods=['GET', 'POST'])
@login_required
def stock_dashboard():
    if current_user.role != 'stock':
        return render_template('unauthorized.html')
    
    form = StockForm()
    if form.validate_on_submit():
        stock = Stock(
            date=datetime.combine(form.date.data, datetime.min.time()),
            product=form.product.data,
            quantity_in=form.quantity_in.data,
            quantity_out=form.quantity_out.data,
            user_id=current_user.id
        )
        db.session.add(stock)
        db.session.commit()
        flash('Stock movement recorded successfully!', 'success')
        return redirect(url_for('stock_dashboard'))
    
    # Calculate available quantities for each product
    stock_movements = Stock.query.all()
    products = {}
    for movement in stock_movements:
        if movement.product not in products:
            products[movement.product] = 0
        products[movement.product] += movement.quantity_in - movement.quantity_out
    
    movements = Stock.query.order_by(Stock.date.desc()).all()
    return render_template('dashboard_stock.html', form=form, movements=movements, products=products)

@app.route('/dashboard/finance')
@login_required
def finance_dashboard():
    if current_user.role != 'finance':
        return render_template('unauthorized.html')
    
    # Get all income and expense records
    records = IncomeExpense.query.all()
    
    # Calculate totals
    total_income = sum(r.amount for r in records if r.type == 'income')
    total_expense = sum(r.amount for r in records if r.type == 'expense')
    balance = total_income - total_expense
    
    return render_template('dashboard_finance.html', 
                          total_income=total_income, 
                          total_expense=total_expense, 
                          balance=balance,
                          records=records)

@app.route('/dashboard/management')
@login_required
def management_dashboard():
    if current_user.role != 'management':
        return render_template('unauthorized.html')
    
    # Financial data
    records = IncomeExpense.query.all()
    total_income = sum(r.amount for r in records if r.type == 'income')
    total_expense = sum(r.amount for r in records if r.type == 'expense')
    balance = total_income - total_expense
    
    # Sales data
    sales = Sale.query.all()
    total_sales = sum(sale.total for sale in sales)
    total_quantity = sum(sale.quantity for sale in sales)
    
    # Stock data - get recent movements (last 20 entries)
    movements = Stock.query.order_by(Stock.date.desc()).limit(20).all()  # Define movements here
    
    # Calculate available quantities for each product
    stock_movements = Stock.query.all()
    products = {}
    for movement in stock_movements:
        if movement.product not in products:
            products[movement.product] = 0
        products[movement.product] += movement.quantity_in - movement.quantity_out
    
    # User data
    users = User.query.all()
    
    return render_template('dashboard_management.html', 
                          total_income=total_income,
                          total_expense=total_expense,
                          balance=balance,
                          total_sales=total_sales,
                          total_quantity=total_quantity,
                          products=products,
                          sales=sales,
                          records=records,
                          users=users,
                          movements=movements)  # Pass movements to template

@app.route('/record/income_expense', methods=['GET', 'POST'])
@login_required
def record_income_expense():
    if current_user.role != 'accounting':
        return render_template('unauthorized.html')
    
    form = IncomeExpenseForm()
    if form.validate_on_submit():
        record = IncomeExpense(
            date=datetime.combine(form.date.data, datetime.min.time()),
            description=form.description.data,
            amount=form.amount.data,
            type=form.type.data,
            user_id=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('Record added successfully!', 'success')
        return redirect(url_for('record_income_expense'))
    
    records = IncomeExpense.query.order_by(IncomeExpense.date.desc()).all()
    return render_template('record_income_expense.html', form=form, records=records)

@app.route('/record/sale', methods=['GET', 'POST'])
@login_required
def record_sale():
    if current_user.role != 'commercial':
        return render_template('unauthorized.html')
    
    form = SaleForm()
    if form.validate_on_submit():
        total = form.quantity.data * form.unit_price.data
        sale = Sale(
            date=datetime.combine(form.date.data, datetime.min.time()),
            product=form.product.data,  # Added product field
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            total=total,
            user_id=current_user.id
        )
        db.session.add(sale)
        db.session.commit()
        flash('Sale recorded successfully!', 'success')
        return redirect(url_for('record_sale'))
    
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return render_template('record_sale.html', form=form, sales=sales)

@app.route('/record/stock', methods=['GET', 'POST'])
@login_required
def record_stock():
    if current_user.role != 'stock':
        return render_template('unauthorized.html')
    
    form = StockForm()
    if form.validate_on_submit():
        stock = Stock(
            date=datetime.combine(form.date.data, datetime.min.time()),
            product=form.product.data,
            quantity_in=form.quantity_in.data,
            quantity_out=form.quantity_out.data,
            user_id=current_user.id  # This ensures we track who made the record
        )
        db.session.add(stock)
        db.session.commit()
        flash('Stock movement recorded successfully!', 'success')
        return redirect(url_for('record_stock'))
    
    # Calculate available quantities for each product
    stock_movements = Stock.query.all()
    products = {}
    for movement in stock_movements:
        if movement.product not in products:
            products[movement.product] = 0
        products[movement.product] += movement.quantity_in - movement.quantity_out
    
    movements = Stock.query.order_by(Stock.date.desc()).all()
    return render_template('record_stock.html', form=form, movements=movements, products=products)

@app.template_filter('format_currency')
def format_currency(value):
    try:
        return "{:,.2f}".format(float(value))  # Example: 12345.6 → 12,345.60
    except (ValueError, TypeError):
        return value

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)