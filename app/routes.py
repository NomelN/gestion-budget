from flask import Blueprint, render_template, request, jsonify
from .models import db, Transaction
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, case

main_routes = Blueprint('main', __name__)

TRANSACTIONS_PER_PAGE = 20

def get_transactions_filtered(limit=None, offset=0):
    query = Transaction.query.filter(Transaction.timestamp <= datetime.utcnow()).order_by(Transaction.id.desc())
    if limit:
        query = query.limit(limit).offset(offset)
    return query.all()

def get_totals_filtered():
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(type="income").filter(Transaction.timestamp <= datetime.utcnow()).scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(type="expense").filter(Transaction.timestamp <= datetime.utcnow()).scalar() or 0
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
    num_installments_str = request.form.get('num_installments')
    num_installments = int(num_installments_str) if num_installments_str else 1

    new_transaction = Transaction(label=label, amount=amount, type=type, is_recurring=is_recurring, recurrence_frequency=recurrence_frequency, total_installments=num_installments if is_recurring else None, paid_installments=1 if is_recurring else 0)
    db.session.add(new_transaction)
    db.session.commit()

    if is_recurring and recurrence_frequency and num_installments > 1:
        # Get the ID of the newly created recurring transaction
        parent_id = new_transaction.id
        current_date = datetime.utcnow()
        for i in range(1, num_installments):
            if recurrence_frequency == 'monthly':
                next_date = current_date + relativedelta(months=i)
            elif recurrence_frequency == 'weekly':
                next_date = current_date + timedelta(weeks=i)
            elif recurrence_frequency == 'yearly':
                next_date = current_date + relativedelta(years=i)
            else:
                break
            
            future_transaction = Transaction(label=label, amount=amount, type=type, timestamp=next_date, is_recurring=False, recurrence_frequency=recurrence_frequency, parent_recurring_id=parent_id)
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

@main_routes.route('/recurring-transactions')
def recurring_transactions():
    recurring_models = Transaction.query.filter_by(is_recurring=True).all()
    # Calculate remaining installments for each recurring model
    for model in recurring_models:
        model.remaining_installments = model.total_installments - model.paid_installments if model.total_installments is not None else None
    return render_template('recurring_transactions.html', recurring_models=recurring_models)

@main_routes.route('/recurring-transaction-details/<int:recurring_model_id>')
def recurring_transaction_details(recurring_model_id):
    recurring_model = Transaction.query.get_or_404(recurring_model_id)
    # Get all future transactions generated by this recurring model
    upcoming_children = Transaction.query.filter(
        Transaction.parent_recurring_id == recurring_model_id,
        Transaction.timestamp > datetime.utcnow()
    ).order_by(Transaction.timestamp.asc()).all()
    return render_template('recurring_transaction_details.html', recurring_model=recurring_model, upcoming_children=upcoming_children)

@main_routes.route('/edit-recurring-transaction/<int:transaction_id>')
def edit_recurring_transaction(transaction_id):
    recurring_model = Transaction.query.get_or_404(transaction_id)
    return render_template('edit_recurring_transaction_form.html', transaction=recurring_model)

@main_routes.route('/update-recurring-transaction/<int:transaction_id>', methods=['PUT'])
def update_recurring_transaction(transaction_id):
    recurring_model = Transaction.query.get_or_404(transaction_id)
    recurring_model.label = request.form['label']
    recurring_model.amount = float(request.form['amount'])
    recurring_model.type = request.form['type']
    recurring_model.recurrence_frequency = request.form['recurrence_frequency']
    db.session.commit()
    return render_template('transaction_item.html', transaction=recurring_model) # Re-render the item in the list

@main_routes.route('/delete-recurring-transaction/<int:transaction_id>', methods=['DELETE'])
def delete_recurring_transaction(transaction_id):
    recurring_model = Transaction.query.get_or_404(transaction_id)
    db.session.delete(recurring_model)
    db.session.commit()
    return '', 200 # Return empty response for HTMX to remove element

@main_routes.route('/upcoming-transactions')
def upcoming_transactions():
    # Get transactions where timestamp is in the future
    upcoming = Transaction.query.filter(Transaction.timestamp > datetime.utcnow()).order_by(Transaction.timestamp.asc()).all()
    # For upcoming transactions that are part of a recurring series, get remaining installments
    for transaction in upcoming:
        if transaction.parent_recurring_id:
            parent_model = Transaction.query.get(transaction.parent_recurring_id)
            if parent_model:
                transaction.remaining_installments = parent_model.total_installments - parent_model.paid_installments
            else:
                transaction.remaining_installments = None
        else:
            transaction.remaining_installments = None
    return render_template('upcoming_transactions.html', upcoming_transactions=upcoming)

@main_routes.route('/pay-in-advance/<int:transaction_id>', methods=['POST'])
def pay_in_advance(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Update the timestamp to now, so it affects the current balance
    transaction.timestamp = datetime.utcnow()
    db.session.commit()

    # If this transaction has a recurring parent, increment its paid_installments
    if transaction.parent_recurring_id:
        parent_recurring_model = Transaction.query.get(transaction.parent_recurring_id)
        if parent_recurring_model:
            parent_recurring_model.paid_installments += 1
            db.session.commit()

    # Recalculate totals and balance for OOB swap
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
    # Return empty response for HTMX to remove the row, plus OOB swaps for balance/totals
    return balance_html + totals_html, 200
