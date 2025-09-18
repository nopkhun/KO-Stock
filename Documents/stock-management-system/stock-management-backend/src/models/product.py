from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(20), nullable=False)  # หน่วยนับ เช่น ชิ้น, กิโลกรัม
    reorder_point = db.Column(db.Integer, default=0)  # จุดสั่งซื้อขั้นต่ำ
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    
    # Foreign Keys
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Relationships
    brand = db.relationship('Brand', backref='products')
    supplier = db.relationship('Supplier', backref='products')
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit': self.unit,
            'reorder_point': self.reorder_point,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'brand_id': self.brand_id,
            'supplier_id': self.supplier_id,
            'brand': self.brand.to_dict() if self.brand else None,
            'supplier': self.supplier.to_dict() if self.supplier else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

