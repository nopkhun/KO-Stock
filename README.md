# Stock Management System

A comprehensive web-based stock management system designed for small businesses with one central warehouse and multiple retail stores. Built with modern technologies including React.js, Flask, and PostgreSQL.

## Features

### Core Functionality
- **Product Management**: Manage products with brands, suppliers, and categories
- **Multi-Location Inventory**: Track stock across central warehouse and multiple stores
- **Stock Operations**: Handle stock-in, transfers, and adjustments
- **Daily Count System**: Physical stock counting with automatic usage calculation
- **Purchase Suggestions**: Automated reorder recommendations grouped by supplier
- **Comprehensive Reports**: Inventory summaries, usage reports, and analytics
- **User Management**: Role-based access control (Admin, Manager, Staff)

### Technical Features
- **Mobile-First Design**: Responsive UI optimized for smartphones and tablets
- **Real-time Updates**: Live inventory tracking and notifications
- **RESTful API**: Clean, documented API endpoints
- **Containerized Deployment**: Docker-based deployment for easy setup
- **Security**: JWT authentication and role-based permissions

## Architecture

### Frontend
- **Framework**: React.js 18+ with Hooks
- **Styling**: Tailwind CSS with shadcn/ui components
- **Routing**: React Router DOM
- **State Management**: Context API with custom hooks
- **HTTP Client**: Axios with interceptors

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL 15
- **Authentication**: JWT tokens
- **API**: RESTful endpoints with proper HTTP status codes
- **Caching**: Redis (optional)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (for frontend)
- **Database**: PostgreSQL with persistent volumes
- **Networking**: Internal Docker network with proper service discovery

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git for cloning the repository
- At least 2GB RAM and 5GB disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-management-system
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:5000
   - Database: localhost:5432

### Default Login Credentials
- **Admin**: username: `admin`, password: `admin123`
- **Manager**: username: `manager`, password: `manager123`
- **Staff**: username: `staff`, password: `staff123`

## Development Setup

### Backend Development
```bash
cd stock-management-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Frontend Development
```bash
cd stock-management-frontend
pnpm install
pnpm run dev
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Product Management
- `GET /api/products` - List all products
- `POST /api/products` - Create new product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Inventory Management
- `GET /api/inventory` - Get inventory by location
- `POST /api/inventory/adjust` - Adjust stock levels
- `GET /api/inventory/location/{id}` - Get inventory for specific location

### Stock Transactions
- `GET /api/stock-transactions` - List transactions
- `POST /api/stock-transactions/stock-in` - Record stock receipt
- `POST /api/stock-transactions/transfer` - Transfer between locations

### Daily Count
- `GET /api/daily-counts` - Get daily count records
- `POST /api/daily-counts` - Submit daily count
- `GET /api/daily-counts/date/{date}` - Get count for specific date

### Reports
- `GET /api/reports/inventory-summary` - Inventory summary report
- `GET /api/reports/purchase-suggestion` - Purchase suggestion report
- `GET /api/reports/usage-summary` - Usage summary report

## Database Schema

### Core Tables
- **users**: User accounts and roles
- **locations**: Warehouses and stores
- **suppliers**: Supplier information
- **brands**: Product brands
- **products**: Product catalog
- **inventory**: Current stock levels by location
- **stock_transactions**: All stock movements
- **daily_counts**: Daily physical count records

### Key Relationships
- Products belong to brands and suppliers
- Inventory tracks products at specific locations
- Stock transactions record all movements
- Daily counts calculate usage automatically

## Deployment

### Production Deployment
1. **Server Requirements**
   - Ubuntu 20.04+ or similar Linux distribution
   - Docker and Docker Compose
   - 4GB RAM minimum, 8GB recommended
   - 20GB disk space minimum

2. **Security Configuration**
   ```bash
   # Update environment variables
   JWT_SECRET_KEY=<strong-random-key>
   POSTGRES_PASSWORD=<secure-password>
   
   # Configure firewall
   ufw allow 80
   ufw allow 443
   ufw enable
   ```

3. **SSL/HTTPS Setup**
   ```bash
   # Add SSL certificates to nginx configuration
   # Update docker-compose.yml for HTTPS
   ```

### Backup Strategy
```bash
# Database backup
docker exec stock_management_db pg_dump -U postgres stock_management > backup.sql

# Volume backup
docker run --rm -v stock_management_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Monitoring and Maintenance

### Health Checks
- All services include Docker health checks
- API endpoints: `/api/health`
- Database connectivity monitoring
- Frontend availability checks

### Logging
- Application logs via Docker logging driver
- Nginx access and error logs
- PostgreSQL query logs (configurable)

### Performance Optimization
- Database indexing on frequently queried columns
- Redis caching for session data
- Nginx gzip compression
- Static asset caching

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database container status
   docker-compose ps database
   
   # View database logs
   docker-compose logs database
   ```

2. **Frontend Build Errors**
   ```bash
   # Clear node modules and reinstall
   cd stock-management-frontend
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   ```

3. **API Not Responding**
   ```bash
   # Check backend container logs
   docker-compose logs backend
   
   # Restart backend service
   docker-compose restart backend
   ```

### Performance Issues
- Monitor container resource usage: `docker stats`
- Check database query performance
- Review nginx access logs for slow requests
- Optimize database queries and add indexes

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with proper testing
4. Submit a pull request with detailed description

### Code Standards
- **Python**: Follow PEP 8 style guide
- **JavaScript**: Use ESLint and Prettier
- **Git**: Conventional commit messages
- **Documentation**: Update README for new features

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For technical support or questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review API documentation
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release with core functionality
- Multi-location inventory management
- Daily count system with usage calculation
- Purchase suggestion automation
- Role-based user management
- Comprehensive reporting system
- Mobile-responsive design
- Docker containerization

