from flask import Blueprint, jsonify, request
from src.models.inventory import Inventory, db
from src.models.product import Product
from src.models.location import Location
from src.models.supplier import Supplier
from src.models.daily_count import DailyCount
from src.models.stock_transaction import StockTransaction
from datetime import datetime, timedelta
from sqlalchemy import func, and_

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/low-stock', methods=['GET'])
def get_low_stock_report():
    """Get products with low stock (below reorder point)"""
    location_id = request.args.get('location_id', type=int)
    
    query = db.session.query(
        Inventory,
        Product,
        Location
    ).join(Product).join(Location).filter(
        Inventory.quantity <= Product.reorder_point
    )
    
    if location_id:
        query = query.filter(Inventory.location_id == location_id)
    
    results = query.all()
    
    low_stock_items = []
    for inventory, product, location in results:
        item = {
            'product_id': product.id,
            'product_name': product.name,
            'sku': product.sku,
            'location_id': location.id,
            'location_name': location.name,
            'current_quantity': inventory.quantity,
            'reorder_point': product.reorder_point,
            'shortage': product.reorder_point - inventory.quantity
        }
        low_stock_items.append(item)
    
    return jsonify(low_stock_items)

@reports_bp.route('/reports/purchase-suggestion', methods=['GET'])
def get_purchase_suggestion():
    """Generate purchase suggestion list grouped by supplier"""
    # Get products with low stock in central warehouse only
    central_warehouse_id = 1  # Assuming central warehouse has ID 1
    
    low_stock_query = db.session.query(
        Inventory,
        Product,
        Supplier
    ).join(Product).join(Supplier, Product.supplier_id == Supplier.id).filter(
        and_(
            Inventory.location_id == central_warehouse_id,
            Inventory.quantity <= Product.reorder_point
        )
    )
    
    results = low_stock_query.all()
    
    # Calculate suggested order quantities based on usage history
    suggestions_by_supplier = {}
    
    for inventory, product, supplier in results:
        # Calculate average daily usage for the last 30 days
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        usage_query = db.session.query(
            func.avg(DailyCount.calculated_usage)
        ).filter(
            and_(
                DailyCount.product_id == product.id,
                DailyCount.count_date >= thirty_days_ago,
                DailyCount.calculated_usage > 0
            )
        )
        
        avg_usage = usage_query.scalar() or 0
        
        # Suggest ordering for 30 days supply
        suggested_quantity = max(
            product.reorder_point - inventory.quantity,  # Minimum to reach reorder point
            int(avg_usage * 30)  # 30 days supply
        )
        
        if supplier.id not in suggestions_by_supplier:
            suggestions_by_supplier[supplier.id] = {
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'supplier_contact': supplier.contact_info,
                'products': []
            }
        
        suggestions_by_supplier[supplier.id]['products'].append({
            'product_id': product.id,
            'product_name': product.name,
            'sku': product.sku,
            'current_quantity': inventory.quantity,
            'reorder_point': product.reorder_point,
            'avg_daily_usage': float(avg_usage),
            'suggested_quantity': suggested_quantity,
            'unit_price': product.unit_price
        })
    
    return jsonify(list(suggestions_by_supplier.values()))

@reports_bp.route('/reports/inventory-movement', methods=['GET'])
def get_inventory_movement_report():
    """Get inventory movement report"""
    location_id = request.args.get('location_id', type=int)
    product_id = request.args.get('product_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400
    
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    query = db.session.query(
        StockTransaction,
        Product,
        Location
    ).join(Product).join(Location).filter(
        and_(
            StockTransaction.created_at >= start_dt,
            StockTransaction.created_at <= end_dt
        )
    )
    
    if location_id:
        query = query.filter(StockTransaction.location_id == location_id)
    
    if product_id:
        query = query.filter(StockTransaction.product_id == product_id)
    
    query = query.order_by(StockTransaction.created_at.desc())
    
    results = query.all()
    
    movements = []
    for transaction, product, location in results:
        movement = transaction.to_dict()
        movement['product'] = product.to_dict()
        movement['location'] = location.to_dict()
        movements.append(movement)
    
    return jsonify(movements)

@reports_bp.route('/reports/stock-summary', methods=['GET'])
def get_stock_summary_report():
    """Get stock summary report by location"""
    query = db.session.query(
        Location.id.label('location_id'),
        Location.name.label('location_name'),
        func.count(Inventory.id).label('total_products'),
        func.sum(Inventory.quantity).label('total_quantity'),
        func.sum(
            func.case([(Inventory.quantity <= Product.reorder_point, 1)], else_=0)
        ).label('low_stock_count'),
        func.sum(
            Product.unit_price * Inventory.quantity
        ).label('total_value')
    ).select_from(Location).outerjoin(Inventory).outerjoin(Product).group_by(
        Location.id, Location.name
    )
    
    results = query.all()
    
    summary = []
    for result in results:
        summary.append({
            'location_id': result.location_id,
            'location_name': result.location_name,
            'total_products': result.total_products or 0,
            'total_quantity': result.total_quantity or 0,
            'low_stock_count': result.low_stock_count or 0,
            'total_value': float(result.total_value or 0)
        })
    
    return jsonify(summary)

@reports_bp.route('/reports/usage-analysis', methods=['GET'])
def get_usage_analysis():
    """Get usage analysis report"""
    location_id = request.args.get('location_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        Product.id.label('product_id'),
        Product.name.label('product_name'),
        Product.sku,
        func.sum(DailyCount.calculated_usage).label('total_usage'),
        func.avg(DailyCount.calculated_usage).label('avg_daily_usage'),
        func.count(DailyCount.id).label('count_days')
    ).select_from(Product).join(DailyCount).filter(
        and_(
            DailyCount.count_date >= start_date,
            DailyCount.count_date <= end_date
        )
    )
    
    if location_id:
        query = query.filter(DailyCount.location_id == location_id)
    
    query = query.group_by(Product.id, Product.name, Product.sku)
    query = query.order_by(func.sum(DailyCount.calculated_usage).desc())
    
    results = query.all()
    
    analysis = []
    for result in results:
        analysis.append({
            'product_id': result.product_id,
            'product_name': result.product_name,
            'sku': result.sku,
            'total_usage': float(result.total_usage or 0),
            'avg_daily_usage': float(result.avg_daily_usage or 0),
            'count_days': result.count_days,
            'usage_trend': 'high' if (result.avg_daily_usage or 0) > 10 else 'medium' if (result.avg_daily_usage or 0) > 5 else 'low'
        })
    
    return jsonify(analysis)

