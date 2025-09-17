from flask import Blueprint, jsonify, request
from src.models.daily_count import DailyCount, db
from src.models.inventory import Inventory
from src.models.stock_transaction import StockTransaction
from datetime import datetime, date

daily_count_bp = Blueprint('daily_count', __name__)

@daily_count_bp.route('/daily-count', methods=['POST'])
def record_daily_count():
    """Record daily physical count and calculate usage"""
    data = request.json
    
    product_id = data['product_id']
    location_id = data['location_id']
    counted_quantity = data['counted_quantity']
    count_date = datetime.fromisoformat(data.get('count_date', datetime.now().isoformat())).date()
    
    # Get current inventory
    inventory = Inventory.query.filter_by(
        product_id=product_id,
        location_id=location_id
    ).first()
    
    if not inventory:
        return jsonify({'error': 'Product not found in this location'}), 404
    
    # Check if count already exists for this date
    existing_count = DailyCount.query.filter_by(
        product_id=product_id,
        location_id=location_id,
        count_date=count_date
    ).first()
    
    if existing_count:
        # Update existing count
        old_usage = existing_count.calculated_usage
        existing_count.counted_quantity = counted_quantity
        existing_count.calculated_usage = inventory.quantity - counted_quantity
        
        # Update inventory
        inventory.quantity = counted_quantity
        
        # Create adjustment transaction for the difference
        usage_diff = existing_count.calculated_usage - old_usage
        if usage_diff != 0:
            transaction = StockTransaction(
                product_id=product_id,
                location_id=location_id,
                transaction_type='daily_usage_adjustment',
                quantity=-usage_diff,
                reference_id=existing_count.id,
                notes=f'Daily count adjustment for {count_date}'
            )
            db.session.add(transaction)
        
        db.session.commit()
        return jsonify(existing_count.to_dict())
    
    else:
        # Calculate usage (starting inventory - counted quantity)
        calculated_usage = inventory.quantity - counted_quantity
        
        # Create new daily count record
        daily_count = DailyCount(
            product_id=product_id,
            location_id=location_id,
            count_date=count_date,
            starting_quantity=inventory.quantity,
            counted_quantity=counted_quantity,
            calculated_usage=calculated_usage
        )
        db.session.add(daily_count)
        
        # Update inventory to counted quantity
        inventory.quantity = counted_quantity
        
        # Create transaction record for usage
        if calculated_usage > 0:
            transaction = StockTransaction(
                product_id=product_id,
                location_id=location_id,
                transaction_type='daily_usage',
                quantity=-calculated_usage,
                reference_id=daily_count.id,
                notes=f'Daily usage for {count_date}'
            )
            db.session.add(transaction)
        
        db.session.commit()
        return jsonify(daily_count.to_dict()), 201

@daily_count_bp.route('/daily-count', methods=['GET'])
def get_daily_counts():
    """Get daily count records"""
    location_id = request.args.get('location_id', type=int)
    product_id = request.args.get('product_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = DailyCount.query
    
    if location_id:
        query = query.filter(DailyCount.location_id == location_id)
    
    if product_id:
        query = query.filter(DailyCount.product_id == product_id)
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date).date()
        query = query.filter(DailyCount.count_date >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date).date()
        query = query.filter(DailyCount.count_date <= end_dt)
    
    query = query.order_by(DailyCount.count_date.desc())
    
    counts = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'daily_counts': [c.to_dict() for c in counts.items],
        'total': counts.total,
        'pages': counts.pages,
        'current_page': page
    })

@daily_count_bp.route('/daily-count/summary', methods=['GET'])
def get_usage_summary():
    """Get usage summary by location and date range"""
    location_id = request.args.get('location_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400
    
    start_dt = datetime.fromisoformat(start_date).date()
    end_dt = datetime.fromisoformat(end_date).date()
    
    query = db.session.query(
        DailyCount.product_id,
        db.func.sum(DailyCount.calculated_usage).label('total_usage'),
        db.func.avg(DailyCount.calculated_usage).label('avg_daily_usage'),
        db.func.count(DailyCount.id).label('count_days')
    ).filter(
        DailyCount.count_date >= start_dt,
        DailyCount.count_date <= end_dt
    )
    
    if location_id:
        query = query.filter(DailyCount.location_id == location_id)
    
    results = query.group_by(DailyCount.product_id).all()
    
    summary = []
    for result in results:
        from src.models.product import Product
        product = Product.query.get(result.product_id)
        summary.append({
            'product_id': result.product_id,
            'product_name': product.name if product else 'Unknown',
            'total_usage': float(result.total_usage or 0),
            'avg_daily_usage': float(result.avg_daily_usage or 0),
            'count_days': result.count_days
        })
    
    return jsonify(summary)

