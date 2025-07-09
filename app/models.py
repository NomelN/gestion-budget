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
