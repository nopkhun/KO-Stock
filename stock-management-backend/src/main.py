import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# Import all models
from src.models.user import db
from src.models.location import Location
from src.models.supplier import Supplier
from src.models.brand import Brand
from src.models.product import Product
from src.models.inventory import Inventory
from src.models.stock_transaction import StockTransaction
from src.models.daily_count import DailyCount

# Import all routes
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.location import location_bp
from src.routes.supplier import supplier_bp
from src.routes.brand import brand_bp
from src.routes.product import product_bp
from src.routes.inventory import inventory_bp
from src.routes.stock_transaction import stock_transaction_bp
from src.routes.daily_count import daily_count_bp
from src.routes.reports import reports_bp
from src.routes.dashboard import dashboard_bp
from routes.health import health_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# Register all blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(location_bp, url_prefix='/api')
app.register_blueprint(supplier_bp, url_prefix='/api')
app.register_blueprint(brand_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')
app.register_blueprint(stock_transaction_bp, url_prefix='/api')
app.register_blueprint(daily_count_bp, url_prefix='/api')
app.register_blueprint(reports_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(health_bp, url_prefix='/api')

# Database configuration
# For development, use SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
# For production with PostgreSQL, uncomment the line below and set environment variables
# app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'stock_management')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and seed initial data
with app.app_context():
    db.create_all()
    
    # Seed initial data if tables are empty
    if Location.query.count() == 0:
        # Create default locations
        central_warehouse = Location(
            name='Central Warehouse',
            location_type='warehouse',
            address='123 Main St, City',
            is_active=True
        )
        store_a = Location(
            name='Store A',
            location_type='store',
            address='456 Store St, City',
            is_active=True
        )
        store_b = Location(
            name='Store B',
            location_type='store',
            address='789 Shop Ave, City',
            is_active=True
        )
        
        db.session.add_all([central_warehouse, store_a, store_b])
        db.session.commit()
        
        # Create default admin user
        from src.models.user import User
        admin_user = User(
            username='admin',
            email='admin@example.com',
            full_name='System Administrator',
            role='admin',
            is_active=True
        )
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("Initial data seeded successfully!")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
