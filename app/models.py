from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# This db object will be initialized in the app factory
# to avoid circular imports.
db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_frequency = db.Column(db.String(10), nullable=True)
    total_installments = db.Column(db.Integer, nullable=True)
    paid_installments = db.Column(db.Integer, default=0)
    parent_recurring_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    # Relationship to access children transactions (generated instances)
    children = db.relationship('Transaction', backref=db.backref('parent', remote_side=[id]), lazy=True)
