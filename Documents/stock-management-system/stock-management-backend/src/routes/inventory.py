from flask import Blueprint, jsonify, request
from src.models.inventory import Inventory, db
from src.models.product import Product
from src.models.location import Location
from sqlalchemy import func

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
    location_id = request.args.get('location_id', type=int)
    search = request.args.get('search', '')
    low_stock = request.args.get('low_stock', type=bool)
    
    query = db.session.query(
        Inventory,
        Product,
        Location
    ).join(Product).join(Location)
    
    if location_id:
        query = query.filter(Inventory.location_id == location_id)
    
    if search:
        query = query.filter(
            (Product.name.contains(search)) |
            (Product.sku.contains(search))
        )
    
    if low_stock:
        query = query.filter(Inventory.quantity <= Product.reorder_point)
    
    results = query.all()
    
    inventory_list = []
    for inventory, product, location in results:
        item = inventory.to_dict()
        item['product'] = product.to_dict()
        item['location'] = location.to_dict()
        inventory_list.append(item)
    
    return jsonify(inventory_list)

@inventory_bp.route('/inventory/<int:product_id>/<int:location_id>', methods=['GET'])
def get_inventory_item(product_id, location_id):
    inventory = Inventory.query.filter_by(
        product_id=product_id, 
        location_id=location_id
    ).first_or_404()
    return jsonify(inventory.to_dict())

@inventory_bp.route('/inventory/adjust', methods=['POST'])
def adjust_inventory():
    """Adjust inventory quantity (for damaged goods, corrections, etc.)"""
    data = request.json
    
    inventory = Inventory.query.filter_by(
        product_id=data['product_id'],
        location_id=data['location_id']
    ).first()
    
    if not inventory:
        inventory = Inventory(
            product_id=data['product_id'],
            location_id=data['location_id'],
            quantity=0
        )
        db.session.add(inventory)
    
    old_quantity = inventory.quantity
    inventory.quantity = data['new_quantity']
    
    # Create transaction record
    from src.models.stock_transaction import StockTransaction
    transaction = StockTransaction(
        product_id=data['product_id'],
        location_id=data['location_id'],
        transaction_type='adjustment',
        quantity=data['new_quantity'] - old_quantity,
        reference_id=None,
        notes=data.get('reason', 'Manual adjustment')
    )
    db.session.add(transaction)
    
    db.session.commit()
    return jsonify(inventory.to_dict())

@inventory_bp.route('/inventory/summary', methods=['GET'])
def get_inventory_summary():
    """Get inventory summary by location"""
    location_id = request.args.get('location_id', type=int)
    
    query = db.session.query(
        Location.name.label('location_name'),
        func.count(Inventory.id).label('total_products'),
        func.sum(Inventory.quantity).label('total_quantity'),
        func.count(
            func.case([(Inventory.quantity <= Product.reorder_point, 1)])
        ).label('low_stock_count')
    ).join(Inventory).join(Product)
    
    if location_id:
        query = query.filter(Location.id == location_id)
    
    results = query.group_by(Location.id, Location.name).all()
    
    summary = []
    for result in results:
        summary.append({
            'location_name': result.location_name,
            'total_products': result.total_products,
            'total_quantity': result.total_quantity,
            'low_stock_count': result.low_stock_count
        })
    
    return jsonify(summary)

