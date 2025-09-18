from flask import Blueprint, jsonify, request
from src.models.stock_transaction import StockTransaction, db
from src.models.inventory import Inventory
from src.models.product import Product
from src.models.location import Location
from datetime import datetime

stock_transaction_bp = Blueprint('stock_transaction', __name__)

@stock_transaction_bp.route('/stock-in', methods=['POST'])
def stock_in():
    """Record stock received at central warehouse"""
    data = request.json
    
    # Create transaction record
    transaction = StockTransaction(
        product_id=data['product_id'],
        location_id=data['location_id'],  # Should be central warehouse
        transaction_type='stock_in',
        quantity=data['quantity'],
        supplier_id=data.get('supplier_id'),
        notes=data.get('notes', '')
    )
    db.session.add(transaction)
    
    # Update inventory
    inventory = Inventory.query.filter_by(
        product_id=data['product_id'],
        location_id=data['location_id']
    ).first()
    
    if not inventory:
        inventory = Inventory(
            product_id=data['product_id'],
            location_id=data['location_id'],
            quantity=data['quantity']
        )
        db.session.add(inventory)
    else:
        inventory.quantity += data['quantity']
    
    db.session.commit()
    return jsonify(transaction.to_dict()), 201

@stock_transaction_bp.route('/stock-transfer', methods=['POST'])
def stock_transfer():
    """Transfer stock from central warehouse to store"""
    data = request.json
    
    from_location_id = data['from_location_id']  # Central warehouse
    to_location_id = data['to_location_id']      # Store
    product_id = data['product_id']
    quantity = data['quantity']
    
    # Check if enough stock in source location
    source_inventory = Inventory.query.filter_by(
        product_id=product_id,
        location_id=from_location_id
    ).first()
    
    if not source_inventory or source_inventory.quantity < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    # Create transfer out transaction
    transfer_out = StockTransaction(
        product_id=product_id,
        location_id=from_location_id,
        transaction_type='transfer_out',
        quantity=-quantity,
        notes=data.get('notes', f'Transfer to location {to_location_id}')
    )
    db.session.add(transfer_out)
    
    # Create transfer in transaction
    transfer_in = StockTransaction(
        product_id=product_id,
        location_id=to_location_id,
        transaction_type='transfer_in',
        quantity=quantity,
        reference_id=transfer_out.id,
        notes=data.get('notes', f'Transfer from location {from_location_id}')
    )
    db.session.add(transfer_in)
    
    # Update source inventory
    source_inventory.quantity -= quantity
    
    # Update destination inventory
    dest_inventory = Inventory.query.filter_by(
        product_id=product_id,
        location_id=to_location_id
    ).first()
    
    if not dest_inventory:
        dest_inventory = Inventory(
            product_id=product_id,
            location_id=to_location_id,
            quantity=quantity
        )
        db.session.add(dest_inventory)
    else:
        dest_inventory.quantity += quantity
    
    db.session.commit()
    return jsonify({
        'transfer_out': transfer_out.to_dict(),
        'transfer_in': transfer_in.to_dict()
    }), 201

@stock_transaction_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get transaction history"""
    location_id = request.args.get('location_id', type=int)
    product_id = request.args.get('product_id', type=int)
    transaction_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = StockTransaction.query
    
    if location_id:
        query = query.filter(StockTransaction.location_id == location_id)
    
    if product_id:
        query = query.filter(StockTransaction.product_id == product_id)
    
    if transaction_type:
        query = query.filter(StockTransaction.transaction_type == transaction_type)
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(StockTransaction.created_at >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(StockTransaction.created_at <= end_dt)
    
    query = query.order_by(StockTransaction.created_at.desc())
    
    transactions = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    })

@stock_transaction_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    transaction = StockTransaction.query.get_or_404(transaction_id)
    return jsonify(transaction.to_dict())

