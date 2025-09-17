from flask import Blueprint, jsonify, request
from src.models.product import Product, db
from src.models.brand import Brand
from src.models.supplier import Supplier

product_bp = Blueprint('product', __name__)

@product_bp.route('/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    brand_id = request.args.get('brand_id', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    
    query = Product.query
    
    if search:
        query = query.filter(
            (Product.name.contains(search)) |
            (Product.sku.contains(search))
        )
    
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)
    
    products = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'products': [product.to_dict() for product in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': page
    })

@product_bp.route('/products', methods=['POST'])
def create_product():
    data = request.json
    product = Product(
        sku=data['sku'],
        name=data['name'],
        brand_id=data['brand_id'],
        supplier_id=data['supplier_id'],
        category=data.get('category'),
        unit=data['unit'],
        reorder_point=data.get('reorder_point', 0),
        image_url=data.get('image_url')
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201

@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    product.sku = data.get('sku', product.sku)
    product.name = data.get('name', product.name)
    product.brand_id = data.get('brand_id', product.brand_id)
    product.supplier_id = data.get('supplier_id', product.supplier_id)
    product.category = data.get('category', product.category)
    product.unit = data.get('unit', product.unit)
    product.reorder_point = data.get('reorder_point', product.reorder_point)
    product.image_url = data.get('image_url', product.image_url)
    db.session.commit()
    return jsonify(product.to_dict())

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return '', 204

