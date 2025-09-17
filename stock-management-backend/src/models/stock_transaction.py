from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class StockTransaction(db.Model):
    __tablename__ = 'stock_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'stock_in', 'transfer', 'adjustment', 'daily_usage'
    quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)  # Null for stock_in
    to_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)    # Null for daily_usage
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='transactions')
    from_location = db.relationship('Location', foreign_keys=[from_location_id], backref='outgoing_transactions')
    to_location = db.relationship('Location', foreign_keys=[to_location_id], backref='incoming_transactions')
    user = db.relationship('User', backref='transactions')
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<StockTransaction {self.transaction_type} Product:{self.product_id} Qty:{self.quantity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'notes': self.notes,
            'product_id': self.product_id,
            'from_location_id': self.from_location_id,
            'to_location_id': self.to_location_id,
            'user_id': self.user_id,
            'product': self.product.to_dict() if self.product else None,
            'from_location': self.from_location.to_dict() if self.from_location else None,
            'to_location': self.to_location.to_dict() if self.to_location else None,
            'user': self.user.to_dict() if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

