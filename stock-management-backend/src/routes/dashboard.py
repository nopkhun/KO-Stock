from flask import Blueprint, jsonify, request
from src.models.inventory import Inventory, db
from src.models.product import Product
from src.models.location import Location
from src.models.daily_count import DailyCount
from src.models.stock_transaction import StockTransaction
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get dashboard overview data"""
    user_location_id = request.args.get('location_id', type=int)
    
    # Total products
    total_products = db.session.query(func.count(Product.id)).scalar()
    
    # Total locations
    total_locations = db.session.query(func.count(Location.id)).scalar()
    
    # Low stock alerts (central warehouse only)
    central_warehouse_id = 1
    low_stock_query = db.session.query(func.count(Inventory.id)).join(Product).filter(
        and_(
            Inventory.location_id == central_warehouse_id,
            Inventory.quantity <= Product.reorder_point
        )
    )
    low_stock_alerts = low_stock_query.scalar()
    
    # Total inventory value
    if user_location_id:
        value_query = db.session.query(
            func.sum(Product.unit_price * Inventory.quantity)
        ).join(Product).filter(Inventory.location_id == user_location_id)
    else:
        value_query = db.session.query(
            func.sum(Product.unit_price * Inventory.quantity)
        ).join(Product)
    
    total_value = value_query.scalar() or 0
    
    # Recent transactions (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_transactions_query = db.session.query(func.count(StockTransaction.id)).filter(
        StockTransaction.created_at >= seven_days_ago
    )
    
    if user_location_id:
        recent_transactions_query = recent_transactions_query.filter(
            StockTransaction.location_id == user_location_id
        )
    
    recent_transactions = recent_transactions_query.scalar()
    
    return jsonify({
        'total_products': total_products,
        'total_locations': total_locations,
        'low_stock_alerts': low_stock_alerts,
        'total_inventory_value': float(total_value),
        'recent_transactions': recent_transactions
    })

@dashboard_bp.route('/dashboard/recent-activities', methods=['GET'])
def get_recent_activities():
    """Get recent activities for dashboard"""
    user_location_id = request.args.get('location_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    query = db.session.query(
        StockTransaction,
        Product,
        Location
    ).join(Product).join(Location).order_by(desc(StockTransaction.created_at))
    
    if user_location_id:
        query = query.filter(StockTransaction.location_id == user_location_id)
    
    query = query.limit(limit)
    results = query.all()
    
    activities = []
    for transaction, product, location in results:
        activity = {
            'id': transaction.id,
            'type': transaction.transaction_type,
            'product_name': product.name,
            'product_sku': product.sku,
            'location_name': location.name,
            'quantity': transaction.quantity,
            'notes': transaction.notes,
            'created_at': transaction.created_at.isoformat(),
            'created_by': transaction.created_by
        }
        activities.append(activity)
    
    return jsonify(activities)

@dashboard_bp.route('/dashboard/low-stock-items', methods=['GET'])
def get_low_stock_items():
    """Get low stock items for dashboard alerts"""
    user_location_id = request.args.get('location_id', type=int)
    limit = request.args.get('limit', 5, type=int)
    
    query = db.session.query(
        Inventory,
        Product,
        Location
    ).join(Product).join(Location).filter(
        Inventory.quantity <= Product.reorder_point
    ).order_by(
        (Inventory.quantity / Product.reorder_point).asc()
    )
    
    if user_location_id:
        query = query.filter(Inventory.location_id == user_location_id)
    
    query = query.limit(limit)
    results = query.all()
    
    low_stock_items = []
    for inventory, product, location in results:
        item = {
            'product_id': product.id,
            'product_name': product.name,
            'sku': product.sku,
            'location_name': location.name,
            'current_quantity': inventory.quantity,
            'reorder_point': product.reorder_point,
            'shortage_percentage': round((1 - inventory.quantity / product.reorder_point) * 100, 1)
        }
        low_stock_items.append(item)
    
    return jsonify(low_stock_items)

@dashboard_bp.route('/dashboard/daily-usage-trend', methods=['GET'])
def get_daily_usage_trend():
    """Get daily usage trend for the last 7 days"""
    user_location_id = request.args.get('location_id', type=int)
    days = 7
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    query = db.session.query(
        DailyCount.count_date,
        func.sum(DailyCount.calculated_usage).label('total_usage')
    ).filter(
        and_(
            DailyCount.count_date >= start_date,
            DailyCount.count_date <= end_date
        )
    )
    
    if user_location_id:
        query = query.filter(DailyCount.location_id == user_location_id)
    
    query = query.group_by(DailyCount.count_date).order_by(DailyCount.count_date)
    
    results = query.all()
    
    # Fill in missing dates with 0 usage
    usage_by_date = {result.count_date: float(result.total_usage or 0) for result in results}
    
    trend_data = []
    current_date = start_date
    while current_date <= end_date:
        trend_data.append({
            'date': current_date.isoformat(),
            'usage': usage_by_date.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    return jsonify(trend_data)

@dashboard_bp.route('/dashboard/top-products', methods=['GET'])
def get_top_products():
    """Get top products by usage in the last 30 days"""
    user_location_id = request.args.get('location_id', type=int)
    limit = request.args.get('limit', 5, type=int)
    
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    
    query = db.session.query(
        Product.id,
        Product.name,
        Product.sku,
        func.sum(DailyCount.calculated_usage).label('total_usage')
    ).join(DailyCount).filter(
        DailyCount.count_date >= thirty_days_ago
    )
    
    if user_location_id:
        query = query.filter(DailyCount.location_id == user_location_id)
    
    query = query.group_by(Product.id, Product.name, Product.sku)
    query = query.order_by(desc(func.sum(DailyCount.calculated_usage)))
    query = query.limit(limit)
    
    results = query.all()
    
    top_products = []
    for result in results:
        product = {
            'product_id': result.id,
            'product_name': result.name,
            'sku': result.sku,
            'total_usage': float(result.total_usage or 0)
        }
        top_products.append(product)
    
    return jsonify(top_products)

