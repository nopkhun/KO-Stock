from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='inventory_records')
    location = db.relationship('Location', backref='inventory_records')
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Unique constraint to ensure one record per product per location
    __table_args__ = (db.UniqueConstraint('product_id', 'location_id', name='unique_product_location'),)

    def __repr__(self):
        return f'<Inventory Product:{self.product_id} Location:{self.location_id} Qty:{self.quantity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'product_id': self.product_id,
            'location_id': self.location_id,
            'product': self.product.to_dict() if self.product else None,
            'location': self.location.to_dict() if self.location else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

