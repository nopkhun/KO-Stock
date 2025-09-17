from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class DailyCount(db.Model):
    __tablename__ = 'daily_counts'
    
    id = db.Column(db.Integer, primary_key=True)
    count_date = db.Column(db.Date, nullable=False)
    counted_quantity = db.Column(db.Integer, nullable=False)
    calculated_usage = db.Column(db.Integer, nullable=True)  # Will be calculated automatically
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='daily_counts')
    location = db.relationship('Location', backref='daily_counts')
    user = db.relationship('User', backref='daily_counts')
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Unique constraint to ensure one count per product per location per day
    __table_args__ = (db.UniqueConstraint('product_id', 'location_id', 'count_date', name='unique_daily_count'),)

    def __repr__(self):
        return f'<DailyCount {self.count_date} Product:{self.product_id} Location:{self.location_id} Count:{self.counted_quantity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'count_date': self.count_date.isoformat() if self.count_date else None,
            'counted_quantity': self.counted_quantity,
            'calculated_usage': self.calculated_usage,
            'product_id': self.product_id,
            'location_id': self.location_id,
            'user_id': self.user_id,
            'product': self.product.to_dict() if self.product else None,
            'location': self.location.to_dict() if self.location else None,
            'user': self.user.to_dict() if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

