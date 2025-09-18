import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Package, 
  Warehouse, 
  TrendingUp, 
  AlertTriangle,
  Users,
  Building2,
  ArrowUp,
  ArrowDown,
  RefreshCw
} from 'lucide-react'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalLocations: 0,
    lowStockItems: 0,
    todayTransactions: 0,
    totalInventoryValue: 0,
    activeUsers: 0
  })

  const [lowStockProducts, setLowStockProducts] = useState([])
  const [recentTransactions, setRecentTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // Simulate API calls - replace with actual API endpoints
      setTimeout(() => {
        setStats({
          totalProducts: 156,
          totalLocations: 6,
          lowStockItems: 12,
          todayTransactions: 28,
          totalInventoryValue: 125000,
          activeUsers: 8
        })

        setLowStockProducts([
          { id: 1, name: 'Product A', currentStock: 5, reorderPoint: 10, location: 'Central Warehouse' },
          { id: 2, name: 'Product B', currentStock: 2, reorderPoint: 15, location: 'Store A' },
          { id: 3, name: 'Product C', currentStock: 8, reorderPoint: 20, location: 'Central Warehouse' },
        ])

        setRecentTransactions([
          { id: 1, type: 'Stock In', product: 'Product X', quantity: 50, location: 'Central Warehouse', time: '10:30 AM' },
          { id: 2, type: 'Transfer', product: 'Product Y', quantity: 25, location: 'Store A → Store B', time: '09:15 AM' },
          { id: 3, type: 'Daily Count', product: 'Product Z', quantity: -3, location: 'Store A', time: '08:45 AM' },
        ])

        setLoading(false)
      }, 1000)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      setLoading(false)
    }
  }

  const StatCard = ({ title, value, icon: Icon, description, trend, trendValue }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend && (
          <div className={`flex items-center text-xs ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
            {trend === 'up' ? <ArrowUp className="h-3 w-3 mr-1" /> : <ArrowDown className="h-3 w-3 mr-1" />}
            {trendValue}
          </div>
        )}
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading dashboard...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Overview of your stock management system</p>
        </div>
        <Button onClick={fetchDashboardData} className="mt-4 sm:mt-0">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Products"
          value={stats.totalProducts}
          icon={Package}
          description="Active products in system"
          trend="up"
          trendValue="+12 this month"
        />
        <StatCard
          title="Locations"
          value={stats.totalLocations}
          icon={Building2}
          description="Warehouses and stores"
        />
        <StatCard
          title="Low Stock Items"
          value={stats.lowStockItems}
          icon={AlertTriangle}
          description="Items below reorder point"
          trend="down"
          trendValue="-3 from yesterday"
        />
        <StatCard
          title="Today's Transactions"
          value={stats.todayTransactions}
          icon={TrendingUp}
          description="Stock movements today"
          trend="up"
          trendValue="+5 from yesterday"
        />
        <StatCard
          title="Inventory Value"
          value={`$${stats.totalInventoryValue.toLocaleString()}`}
          icon={Warehouse}
          description="Total inventory worth"
          trend="up"
          trendValue="+2.5% this week"
        />
        <StatCard
          title="Active Users"
          value={stats.activeUsers}
          icon={Users}
          description="Users logged in today"
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Alert */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 text-orange-500" />
              Low Stock Alert
            </CardTitle>
            <CardDescription>
              Products that need immediate attention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {lowStockProducts.map((product) => (
                <div key={product.id} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{product.name}</p>
                    <p className="text-sm text-gray-600">{product.location}</p>
                  </div>
                  <div className="text-right">
                    <Badge variant="destructive" className="mb-1">
                      {product.currentStock} left
                    </Badge>
                    <p className="text-xs text-gray-500">
                      Reorder at {product.reorderPoint}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              View All Low Stock Items
            </Button>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2 text-blue-500" />
              Recent Transactions
            </CardTitle>
            <CardDescription>
              Latest stock movements and activities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentTransactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{transaction.product}</p>
                    <p className="text-sm text-gray-600">{transaction.location}</p>
                  </div>
                  <div className="text-right">
                    <Badge 
                      variant={transaction.type === 'Stock In' ? 'default' : transaction.type === 'Transfer' ? 'secondary' : 'outline'}
                      className="mb-1"
                    >
                      {transaction.type}
                    </Badge>
                    <p className="text-xs text-gray-500">
                      {transaction.quantity > 0 ? '+' : ''}{transaction.quantity} • {transaction.time}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              View All Transactions
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard

