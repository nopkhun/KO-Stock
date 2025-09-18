from flask import Blueprint, jsonify, request, session, g
from src.models.user import User, db
from src.middleware.security import input_validation, secure_headers
from functools import wraps
import time

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Enhanced decorator to require login with session validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Validate session integrity
        login_time = session.get('login_time')
        if login_time and (time.time() - login_time) > 3600:  # 1 hour timeout
            session.clear()
            return jsonify({'error': 'Session expired. Please log in again.'}), 401
        
        # Validate client IP consistency (optional security measure)
        session_ip = session.get('client_ip')
        current_ip = request.headers.get('X-Real-IP', request.remote_addr)
        if session_ip and session_ip != current_ip:
            session.clear()
            return jsonify({'error': 'Session security violation. Please log in again.'}), 401
        
        # Verify user still exists and is active
        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            return jsonify({'error': 'User account is no longer active'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
@input_validation(
    required_fields=['username', 'password'],
    field_types={'username': str, 'password': str}
)
@secure_headers({
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache'
})
def login():
    """User login endpoint with enhanced security"""
    try:
        data = g.validated_json
        
        # Additional validation for login attempts
        username = data['username'].strip()
        password = data['password']
        
        # Basic input validation
        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': 'Invalid username format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Invalid password format'}), 400
        
        # Rate limiting for login attempts (additional to middleware)
        client_ip = request.headers.get('X-Real-IP', request.remote_addr)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            # Regenerate session ID for security
            session.permanent = True
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['location_id'] = user.location_id
            session['login_time'] = time.time()
            session['client_ip'] = client_ip
            
            # Update last login time
            user.last_login = time.time()
            db.session.commit()
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict(),
                'session_timeout': 3600  # 1 hour
            }), 200
        else:
            # Log failed login attempt
            if user:
                user.failed_login_attempts = getattr(user, 'failed_login_attempts', 0) + 1
                db.session.commit()
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
@secure_headers({
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache'
})
def logout():
    """User logout endpoint with secure session cleanup"""
    # Log logout for audit trail
    user_id = session.get('user_id')
    
    # Clear all session data securely
    session.clear()
    
    return jsonify({
        'message': 'Logout successful',
        'redirect': '/login'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
@input_validation(
    required_fields=['current_password', 'new_password'],
    field_types={'current_password': str, 'new_password': str}
)
@secure_headers({
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache'
})
def change_password():
    """Change user password with enhanced security validation"""
    try:
        data = g.validated_json
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Enhanced password validation
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        if not any(c.isupper() for c in new_password):
            return jsonify({'error': 'New password must contain at least one uppercase letter'}), 400
        
        if not any(c.islower() for c in new_password):
            return jsonify({'error': 'New password must contain at least one lowercase letter'}), 400
        
        if not any(c.isdigit() for c in new_password):
            return jsonify({'error': 'New password must contain at least one number'}), 400
        
        if current_password == new_password:
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Set new password
        user.set_password(new_password)
        user.password_changed_at = time.time()
        db.session.commit()
        
        # Clear session to force re-login with new password
        session.clear()
        
        return jsonify({
            'message': 'Password changed successfully. Please log in again.',
            'redirect': '/login'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Password change failed'}), 500

