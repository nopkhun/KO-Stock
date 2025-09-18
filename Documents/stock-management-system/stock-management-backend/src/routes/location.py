from flask import Blueprint, jsonify, request
from src.models.location import Location, db
from src.routes.auth import login_required, admin_required

location_bp = Blueprint('location', __name__)

@location_bp.route('/locations', methods=['GET'])
@login_required
def get_locations():
    """Get all locations"""
    try:
        locations = Location.query.filter_by(is_active=True).all()
        return jsonify([location.to_dict() for location in locations]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/locations', methods=['POST'])
@admin_required
def create_location():
    """Create new location"""
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('type'):
            return jsonify({'error': 'Name and type are required'}), 400
        
        location = Location(
            name=data['name'],
            type=data['type'],
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(location)
        db.session.commit()
        
        return jsonify(location.to_dict()), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/locations/<int:location_id>', methods=['GET'])
@login_required
def get_location(location_id):
    """Get specific location"""
    try:
        location = Location.query.get_or_404(location_id)
        return jsonify(location.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/locations/<int:location_id>', methods=['PUT'])
@admin_required
def update_location(location_id):
    """Update location"""
    try:
        location = Location.query.get_or_404(location_id)
        data = request.get_json()
        
        if data.get('name'):
            location.name = data['name']
        if data.get('type'):
            location.type = data['type']
        if 'address' in data:
            location.address = data['address']
        if 'phone' in data:
            location.phone = data['phone']
        if 'is_active' in data:
            location.is_active = data['is_active']
        
        db.session.commit()
        return jsonify(location.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/locations/<int:location_id>', methods=['DELETE'])
@admin_required
def delete_location(location_id):
    """Soft delete location"""
    try:
        location = Location.query.get_or_404(location_id)
        location.is_active = False
        db.session.commit()
        return jsonify({'message': 'Location deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

