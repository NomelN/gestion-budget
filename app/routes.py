from flask import Blueprint, render_template, request, jsonify
from .models import db, Transaction
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, case

main_routes = Blueprint('main', __name__)

TRANSACTIONS_PER_PAGE = 20

def get_transactions_filtered(limit=None, offset=0):
    query = Transaction.query.order_by(Transaction.id.desc())
    if limit:
        query = query.limit(limit).offset(offset)
    return query.all()

def get_totals_filtered():
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(type="income").scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(type="expense").scalar() or 0
    return total_income, total_expense

@main_routes.route('/')
def index():
    transactions = get_transactions_filtered(limit=TRANSACTIONS_PER_PAGE)
    total_income, total_expense = get_totals_filtered()
    balance = total_income - total_expense
    total_transactions_count = Transaction.query.count()
    has_more = total_transactions_count > TRANSACTIONS_PER_PAGE

    return render_template('index.html', 
                           transactions=transactions, 
                           balance=balance, 
                           has_more=has_more, 
                           current_offset=TRANSACTIONS_PER_PAGE,
                           total_income=total_income,
                           total_expense=total_expense)

@main_routes.route('/transactions')
def load_transactions():
    offset = int(request.args.get('offset', 0))
    transactions = get_transactions_filtered(limit=TRANSACTIONS_PER_PAGE, offset=offset)
    total_transactions_count = Transaction.query.count()
    next_offset = offset + TRANSACTIONS_PER_PAGE
    has_more = total_transactions_count > next_offset
    return render_template('transactions_list.html', transactions=transactions, next_offset=next_offset, has_more=has_more)

@main_routes.route('/add-transaction', methods=['POST'])
def add_transaction():
    label = request.form['label']
    amount = float(request.form['amount'])
    type = request.form['type']
    is_recurring = request.form.get('is_recurring') == '1'
    recurrence_frequency = request.form.get('recurrence_frequency')
    num_installments = int(request.form.get('num_installments', 1))

    new_transaction = Transaction(label=label, amount=amount, type=type, is_recurring=is_recurring, recurrence_frequency=recurrence_frequency)
    db.session.add(new_transaction)
    db.session.commit()

    if is_recurring and recurrence_frequency and num_installments > 1:
        current_date = datetime.utcnow()
        for i in range(1, num_installments):
            if recurrence_frequency == 'monthly':
                next_date = current_date + relativedelta(months=i)
            elif recurrence_frequency == 'weekly':
                next_date = current_date + relativedelta(weeks=i)
            elif recurrence_frequency == 'yearly':
                next_date = current_date + relativedelta(years=i)
            else:
                break
            
            future_transaction = Transaction(label=label, amount=amount, type=type, timestamp=next_date, is_recurring=False, recurrence_frequency=recurrence_frequency)
            db.session.add(future_transaction)
        db.session.commit()
    
    total_income, total_expense = get_totals_filtered()
    balance = total_income - total_expense

    balance_html = f'''
    <div id="balance" hx-swap-oob="true" class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg mb-10 text-center">
        <h2 class="text-lg font-medium text-indigo-200">Solde Actuel</h2>
        <p class="text-4xl font-bold tracking-tight">{balance:.2f} €</p>
    </div>
    '''
    totals_html = f'''
    <div id="totals-by-type" hx-swap-oob="true" class="grid grid-cols-2 gap-4 text-center">
        <div class="bg-green-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Revenus</h3>
            <p class="text-2xl font-bold">{total_income:.2f} €</p>
        </div>
        <div class="bg-rose-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Dépenses</h3>
            <p class="text-2xl font-bold">{total_expense:.2f} €</p>
        </div>
    </div>
    '''
    transaction_html = render_template('transaction_item.html', transaction=new_transaction)
    return transaction_html + balance_html + totals_html

@main_routes.route('/delete-transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    
    total_income, total_expense = get_totals_filtered()
    balance = total_income - total_expense

    balance_html = f'''
    <div id="balance" hx-swap-oob="true" class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg mb-10 text-center">
        <h2 class="text-lg font-medium text-indigo-200">Solde Actuel</h2>
        <p class="text-4xl font-bold tracking-tight">{balance:.2f} €</p>
    </div>
    '''
    totals_html = f'''
    <div id="totals-by-type" hx-swap-oob="true" class="grid grid-cols-2 gap-4 text-center">
        <div class="bg-green-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Revenus</h3>
            <p class="text-2xl font-bold">{total_income:.2f} €</p>
        </div>
        <div class="bg-rose-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Dépenses</h3>
            <p class="text-2xl font-bold">{total_expense:.2f} €</p>
        </div>
    </div>
    '''
    return balance_html + totals_html

@main_routes.route('/edit-transaction/<int:transaction_id>')
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    return render_template('edit_transaction_form.html', transaction=transaction)

@main_routes.route('/update-transaction/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    transaction.label = request.form['label']
    transaction.amount = float(request.form['amount'])
    transaction.type = request.form['type']
    db.session.commit()
    
    total_income, total_expense = get_totals_filtered()
    balance = total_income - total_expense

    balance_html = f'''
    <div id="balance" hx-swap-oob="true" class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg mb-10 text-center">
        <h2 class="text-lg font-medium text-indigo-200">Solde Actuel</h2>
        <p class="text-4xl font-bold tracking-tight">{balance:.2f} €</p>
    </div>
    '''
    totals_html = f'''
    <div id="totals-by-type" hx-swap-oob="true" class="grid grid-cols-2 gap-4 text-center">
        <div class="bg-green-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Revenus</h3>
            <p class="text-2xl font-bold">{total_income:.2f} €</p>
        </div>
        <div class="bg-rose-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Dépenses</h3>
            <p class="text-2xl font-bold">{total_expense:.2f} €</p>
        </div>
    </div>
    '''
    transaction_html = render_template('transaction_item.html', transaction=transaction)
    return transaction_html + balance_html + totals_html

@main_routes.route('/get-transaction/<int:transaction_id>')
def get_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    return render_template('transaction_item.html', transaction=transaction)

@main_routes.route('/totals-by-type')
def totals_by_type():
    total_income, total_expense = get_totals_filtered()
    return f'''
    <div id="totals-by-type" hx-swap-oob="true" class="grid grid-cols-2 gap-4 text-center">
        <div class="bg-green-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Revenus</h3>
            <p class="text-2xl font-bold">{total_income:.2f} €</p>
        </div>
        <div class="bg-rose-500 text-white p-4 rounded-lg shadow-md">
            <h3 class="text-lg font-medium">Dépenses</h3>
            <p class="text-2xl font-bold">{total_expense:.2f} €</p>
        </div>
    </div>
    '''

@main_routes.route('/reports')
def reports():
    monthly_data = db.session.query(
        extract('year', Transaction.timestamp).label('year'),
        extract('month', Transaction.timestamp).label('month'),
        db.func.sum(case((Transaction.type == 'income', Transaction.amount), else_=0)).label('total_income'),
        db.func.sum(case((Transaction.type == 'expense', Transaction.amount), else_=0)).label('total_expense')
    ).group_by('year', 'month').order_by(db.desc('year'), db.desc('month')).all()

    labels = [f"{datetime(r.year, r.month, 1).strftime('%b')} {r.year}" for r in monthly_data]
    income_data = [r.total_income for r in monthly_data]
    expense_data = [r.total_expense for r in monthly_data]
    
    labels.reverse()
    income_data.reverse()
    expense_data.reverse()

    num_months = len(monthly_data)
    total_income = sum(income_data)
    total_expense = sum(expense_data)
    avg_income = total_income / num_months if num_months > 0 else 0
    avg_expense = total_expense / num_months if num_months > 0 else 0
    net_balance = total_income - total_expense

    summary_stats = {
        'total_income': total_income,
        'total_expense': total_expense,
        'avg_income': avg_income,
        'avg_expense': avg_expense,
        'net_balance': net_balance,
        'num_months': num_months
    }

    chart_data = {
        "labels": labels,
        "income": income_data,
        "expense": expense_data
    }

    return render_template('reports.html', monthly_data=monthly_data, chart_data=chart_data, summary=summary_stats)
