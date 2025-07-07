from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

TRANSACTIONS_PER_PAGE = 20

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    transactions = conn.execute(f'SELECT * FROM transactions ORDER BY id DESC LIMIT {TRANSACTIONS_PER_PAGE}').fetchall()
    balance = conn.execute('SELECT SUM(CASE WHEN type = "income" THEN amount ELSE -amount END) FROM transactions').fetchone()[0] or 0
    total_transactions = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
    conn.close()
    has_more = total_transactions > TRANSACTIONS_PER_PAGE
    return render_template('index.html', transactions=transactions, balance=balance, has_more=has_more, current_offset=TRANSACTIONS_PER_PAGE)

@app.route('/transactions')
def load_transactions():
    offset = int(request.args.get('offset', 0))
    conn = get_db_connection()
    transactions = conn.execute(f'SELECT * FROM transactions ORDER BY id DESC LIMIT {TRANSACTIONS_PER_PAGE} OFFSET {offset}').fetchall()
    total_transactions = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
    conn.close()
    next_offset = offset + TRANSACTIONS_PER_PAGE
    has_more = total_transactions > next_offset
    return render_template('transactions_list.html', transactions=transactions, next_offset=next_offset, has_more=has_more)

@app.route('/add-transaction', methods=['POST'])
def add_transaction():
    conn = get_db_connection()
    label = request.form['label']
    amount = float(request.form['amount'])
    type = request.form['type']
    conn.execute('INSERT INTO transactions (label, amount, type) VALUES (?, ?, ?)', (label, amount, type))
    conn.commit()
    transaction = conn.execute('SELECT * FROM transactions ORDER BY id DESC LIMIT 1').fetchone()
    balance = conn.execute('SELECT SUM(CASE WHEN type = "income" THEN amount ELSE -amount END) FROM transactions').fetchone()[0] or 0
    conn.close()

    balance_html = f'''
    <div id="balance" hx-swap-oob="true" class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg mb-10 text-center">
        <h2 class="text-lg font-medium text-indigo-200">Solde Actuel</h2>
        <p class="text-4xl font-bold tracking-tight">{balance:.2f} €</p>
    </div>
    '''
    transaction_html = render_template('transaction_item.html', transaction=transaction)
    return transaction_html + balance_html

@app.route('/delete-transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    balance = conn.execute('SELECT SUM(CASE WHEN type = "income" THEN amount ELSE -amount END) FROM transactions').fetchone()[0] or 0
    conn.close()
    balance_html = f'''
    <div id="balance" hx-swap-oob="true" class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg mb-10 text-center">
        <h2 class="text-lg font-medium text-indigo-200">Solde Actuel</h2>
        <p class="text-4xl font-bold tracking-tight">{balance:.2f} €</p>
    </div>
    '''
    return balance_html

@app.route('/edit-transaction/<int:transaction_id>')
def edit_transaction(transaction_id):
    conn = get_db_connection()
    transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    conn.close()
    return render_template('edit_transaction_form.html', transaction=transaction)

@app.route('/update-transaction/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    conn = get_db_connection()
    label = request.form['label']
    amount = float(request.form['amount'])
    type = request.form['type']
    conn.execute('UPDATE transactions SET label = ?, amount = ?, type = ? WHERE id = ?', (label, amount, type, transaction_id))
    conn.commit()
    transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    balance = conn.execute('SELECT SUM(CASE WHEN type = "income" THEN amount ELSE -amount END) FROM transactions').fetchone()[0] or 0
    conn.close()

    balance_html = f'''
    <div id="balance" hx-swap-oob="true" class="bg-indigo-600 text-white p-6 rounded-2xl shadow-lg mb-10 text-center">
        <h2 class="text-lg font-medium text-indigo-200">Solde Actuel</h2>
        <p class="text-4xl font-bold tracking-tight">{balance:.2f} €</p>
    </div>
    '''
    transaction_html = render_template('transaction_item.html', transaction=transaction)
    return transaction_html + balance_html

@app.route('/get-transaction/<int:transaction_id>')
def get_transaction(transaction_id):
    conn = get_db_connection()
    transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,)).fetchone()
    conn.close()
    return render_template('transaction_item.html', transaction=transaction)

@app.route('/chart-data')
def chart_data():
    conn = get_db_connection()
    total_income = conn.execute('SELECT SUM(amount) FROM transactions WHERE type = "income"').fetchone()[0] or 0
    total_expense = conn.execute('SELECT SUM(amount) FROM transactions WHERE type = "expense"').fetchone()[0] or 0
    conn.close()
    return {
        'labels': ['Revenus', 'Dépenses'],
        'data': [total_income, total_expense],
        'colors': ['#4CAF50', '#F44336'] # Green for income, Red for expense
    }

if __name__ == '__main__':
    app.run(debug=True)
