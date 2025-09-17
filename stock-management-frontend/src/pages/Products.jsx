import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Package,
  Filter,
  RefreshCw
} from 'lucide-react'

const Products = () => {
  const [products, setProducts] = useState([])
  const [brands, setBrands] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedBrand, setSelectedBrand] = useState('')
  const [selectedSupplier, setSelectedSupplier] = useState('')
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)

  const [newProduct, setNewProduct] = useState({
    sku: '',
    name: '',
    brand_id: '',
    supplier_id: '',
    category: '',
    unit: '',
    reorder_point: '',
    description: ''
  })

  useEffect(() => {
    fetchProducts()
    fetchBrands()
    fetchSuppliers()
  }, [])

  const fetchProducts = async () => {
    setLoading(true)
    try {
      // Simulate API call - replace with actual API
      setTimeout(() => {
        setProducts([
          {
            id: 1,
            sku: 'PRD001',
            name: 'Product A',
            brand: 'Brand X',
            supplier: 'Supplier 1',
            category: 'Electronics',
            unit: 'pcs',
            reorder_point: 10,
            current_stock: 25,
            description: 'High-quality electronic product'
          },
          {
            id: 2,
            sku: 'PRD002',
            name: 'Product B',
            brand: 'Brand Y',
            supplier: 'Supplier 2',
            category: 'Accessories',
            unit: 'pcs',
            reorder_point: 15,
            current_stock: 8,
            description: 'Premium accessory item'
          },
          {
            id: 3,
            sku: 'PRD003',
            name: 'Product C',
            brand: 'Brand X',
            supplier: 'Supplier 1',
            category: 'Electronics',
            unit: 'box',
            reorder_point: 20,
            current_stock: 45,
            description: 'Essential electronic component'
          }
        ])
        setLoading(false)
      }, 1000)
    } catch (error) {
      console.error('Error fetching products:', error)
      setLoading(false)
    }
  }

  const fetchBrands = async () => {
    // Simulate API call
    setBrands([
      { id: 1, name: 'Brand X' },
      { id: 2, name: 'Brand Y' },
      { id: 3, name: 'Brand Z' }
    ])
  }

  const fetchSuppliers = async () => {
    // Simulate API call
    setSuppliers([
      { id: 1, name: 'Supplier 1' },
      { id: 2, name: 'Supplier 2' },
      { id: 3, name: 'Supplier 3' }
    ])
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setNewProduct(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      // Simulate API call
      const productData = {
        ...newProduct,
        id: editingProduct ? editingProduct.id : Date.now(),
        brand: brands.find(b => b.id === parseInt(newProduct.brand_id))?.name || '',
        supplier: suppliers.find(s => s.id === parseInt(newProduct.supplier_id))?.name || '',
        current_stock: editingProduct ? editingProduct.current_stock : 0
      }

      if (editingProduct) {
        setProducts(prev => prev.map(p => p.id === editingProduct.id ? productData : p))
      } else {
        setProducts(prev => [...prev, productData])
      }

      resetForm()
      setIsAddDialogOpen(false)
    } catch (error) {
      console.error('Error saving product:', error)
    }
  }

  const resetForm = () => {
    setNewProduct({
      sku: '',
      name: '',
      brand_id: '',
      supplier_id: '',
      category: '',
      unit: '',
      reorder_point: '',
      description: ''
    })
    setEditingProduct(null)
  }

  const handleEdit = (product) => {
    setEditingProduct(product)
    setNewProduct({
      sku: product.sku,
      name: product.name,
      brand_id: brands.find(b => b.name === product.brand)?.id?.toString() || '',
      supplier_id: suppliers.find(s => s.name === product.supplier)?.id?.toString() || '',
      category: product.category,
      unit: product.unit,
      reorder_point: product.reorder_point.toString(),
      description: product.description
    })
    setIsAddDialogOpen(true)
  }

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      setProducts(prev => prev.filter(p => p.id !== productId))
    }
  }

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.sku.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesBrand = !selectedBrand || product.brand === selectedBrand
    const matchesSupplier = !selectedSupplier || product.supplier === selectedSupplier
    
    return matchesSearch && matchesBrand && matchesSupplier
  })

  const getStockStatus = (currentStock, reorderPoint) => {
    if (currentStock === 0) return { status: 'Out of Stock', variant: 'destructive' }
    if (currentStock <= reorderPoint) return { status: 'Low Stock', variant: 'secondary' }
    return { status: 'In Stock', variant: 'default' }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600">Manage your product catalog</p>
        </div>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm} className="mt-4 sm:mt-0">
              <Plus className="h-4 w-4 mr-2" />
              Add Product
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{editingProduct ? 'Edit Product' : 'Add New Product'}</DialogTitle>
              <DialogDescription>
                {editingProduct ? 'Update product information' : 'Enter product details to add to catalog'}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="sku">SKU</Label>
                  <Input
                    id="sku"
                    name="sku"
                    value={newProduct.sku}
                    onChange={handleInputChange}
                    placeholder="PRD001"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="unit">Unit</Label>
                  <Input
                    id="unit"
                    name="unit"
                    value={newProduct.unit}
                    onChange={handleInputChange}
                    placeholder="pcs, box, kg"
                    required
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="name">Product Name</Label>
                <Input
                  id="name"
                  name="name"
                  value={newProduct.name}
                  onChange={handleInputChange}
                  placeholder="Enter product name"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="brand_id">Brand</Label>
                  <Select value={newProduct.brand_id} onValueChange={(value) => setNewProduct(prev => ({...prev, brand_id: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select brand" />
                    </SelectTrigger>
                    <SelectContent>
                      {brands.map(brand => (
                        <SelectItem key={brand.id} value={brand.id.toString()}>
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="supplier_id">Supplier</Label>
                  <Select value={newProduct.supplier_id} onValueChange={(value) => setNewProduct(prev => ({...prev, supplier_id: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select supplier" />
                    </SelectTrigger>
                    <SelectContent>
                      {suppliers.map(supplier => (
                        <SelectItem key={supplier.id} value={supplier.id.toString()}>
                          {supplier.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    name="category"
                    value={newProduct.category}
                    onChange={handleInputChange}
                    placeholder="Electronics, Accessories"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="reorder_point">Reorder Point</Label>
                  <Input
                    id="reorder_point"
                    name="reorder_point"
                    type="number"
                    value={newProduct.reorder_point}
                    onChange={handleInputChange}
                    placeholder="10"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  name="description"
                  value={newProduct.description}
                  onChange={handleInputChange}
                  placeholder="Product description"
                />
              </div>

              <div className="flex gap-2 pt-4">
                <Button type="submit" className="flex-1">
                  {editingProduct ? 'Update Product' : 'Add Product'}
                </Button>
                <Button type="button" variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search products by name or SKU..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={selectedBrand} onValueChange={setSelectedBrand}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="All Brands" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Brands</SelectItem>
                  {brands.map(brand => (
                    <SelectItem key={brand.id} value={brand.name}>
                      {brand.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedSupplier} onValueChange={setSelectedSupplier}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="All Suppliers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Suppliers</SelectItem>
                  {suppliers.map(supplier => (
                    <SelectItem key={supplier.id} value={supplier.name}>
                      {supplier.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={fetchProducts}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Products Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading products...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map((product) => {
            const stockStatus = getStockStatus(product.current_stock, product.reorder_point)
            return (
              <Card key={product.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{product.name}</CardTitle>
                      <CardDescription>{product.sku}</CardDescription>
                    </div>
                    <Package className="h-5 w-5 text-gray-400" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Brand:</span>
                      <span className="font-medium">{product.brand}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Supplier:</span>
                      <span className="font-medium">{product.supplier}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Category:</span>
                      <span className="font-medium">{product.category}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Current Stock:</span>
                      <Badge variant={stockStatus.variant}>
                        {product.current_stock} {product.unit}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Reorder Point:</span>
                      <span className="font-medium">{product.reorder_point} {product.unit}</span>
                    </div>
                    {product.description && (
                      <p className="text-sm text-gray-600 mt-2">{product.description}</p>
                    )}
                  </div>
                  
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(product)}
                      className="flex-1"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(product.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {filteredProducts.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No products found</h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || selectedBrand || selectedSupplier
                ? 'Try adjusting your search criteria'
                : 'Get started by adding your first product'
              }
            </p>
            {!searchTerm && !selectedBrand && !selectedSupplier && (
              <Button onClick={() => setIsAddDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Product
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Products

