from flask import Blueprint, jsonify, request
from src.models.brand import Brand, db

brand_bp = Blueprint('brand', __name__)

@brand_bp.route('/brands', methods=['GET'])
def get_brands():
    brands = Brand.query.all()
    return jsonify([brand.to_dict() for brand in brands])

@brand_bp.route('/brands', methods=['POST'])
def create_brand():
    data = request.json
    brand = Brand(
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(brand)
    db.session.commit()
    return jsonify(brand.to_dict()), 201

@brand_bp.route('/brands/<int:brand_id>', methods=['GET'])
def get_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    return jsonify(brand.to_dict())

@brand_bp.route('/brands/<int:brand_id>', methods=['PUT'])
def update_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    data = request.json
    brand.name = data.get('name', brand.name)
    brand.description = data.get('description', brand.description)
    db.session.commit()
    return jsonify(brand.to_dict())

@brand_bp.route('/brands/<int:brand_id>', methods=['DELETE'])
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    db.session.delete(brand)
    db.session.commit()
    return '', 204

