import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { 
  Menu, 
  X, 
  Home, 
  Package, 
  Warehouse, 
  TrendingUp, 
  Users, 
  Settings,
  LogOut,
  Building2,
  Truck,
  ClipboardList,
  BarChart3
} from 'lucide-react'
import './Layout.css'

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  const menuItems = [
    { path: '/', icon: Home, label: 'Dashboard', roles: ['admin', 'manager', 'staff'] },
    { path: '/products', icon: Package, label: 'Products', roles: ['admin', 'manager', 'staff'] },
    { path: '/inventory', icon: Warehouse, label: 'Inventory', roles: ['admin', 'manager', 'staff'] },
    { path: '/stock-in', icon: TrendingUp, label: 'Stock In', roles: ['admin', 'manager'] },
    { path: '/transfer', icon: Truck, label: 'Transfer', roles: ['admin', 'manager', 'staff'] },
    { path: '/daily-count', icon: ClipboardList, label: 'Daily Count', roles: ['admin', 'manager', 'staff'] },
    { path: '/reports', icon: BarChart3, label: 'Reports', roles: ['admin', 'manager'] },
    { path: '/locations', icon: Building2, label: 'Locations', roles: ['admin'] },
    { path: '/users', icon: Users, label: 'Users', roles: ['admin'] },
    { path: '/settings', icon: Settings, label: 'Settings', roles: ['admin', 'manager', 'staff'] },
  ]

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const isActive = (path) => {
    return location.pathname === path
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white shadow-sm border-b px-4 py-3 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Stock Management</h1>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </Button>
      </div>

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 px-4 bg-blue-600 text-white">
            <Package className="h-8 w-8 mr-2" />
            <span className="text-lg font-semibold hidden lg:block">Stock Management</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {menuItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <item.icon className="h-5 w-5 mr-3" />
                {item.label}
              </Link>
            ))}
          </nav>

          {/* User Info & Logout */}
          <div className="p-4 border-t">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                A
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">Admin User</p>
                <p className="text-xs text-gray-500">Administrator</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:pl-64">
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}

export default Layout

