import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, ArrowUpDown, Package, TrendingUp, TrendingDown } from 'lucide-react';
import axios from 'axios';

const StockTransactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [products, setProducts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  
  const [newTransaction, setNewTransaction] = useState({
    type: 'stock_in',
    product_id: '',
    from_location_id: '',
    to_location_id: '',
    quantity: '',
    supplier_id: '',
    notes: ''
  });

  useEffect(() => {
    fetchTransactions();
    fetchProducts();
    fetchLocations();
    fetchSuppliers();
  }, []);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/stock-transactions');
      setTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get('/api/products');
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get('/api/locations');
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get('/api/suppliers');
      setSuppliers(response.data);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/stock-transactions', newTransaction);
      setIsDialogOpen(false);
      setNewTransaction({
        type: 'stock_in',
        product_id: '',
        from_location_id: '',
        to_location_id: '',
        quantity: '',
        supplier_id: '',
        notes: ''
      });
      fetchTransactions();
    } catch (error) {
      console.error('Error creating transaction:', error);
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'stock_in':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'transfer':
        return <ArrowUpDown className="h-4 w-4 text-blue-600" />;
      case 'adjustment':
        return <Package className="h-4 w-4 text-orange-600" />;
      default:
        return <Package className="h-4 w-4" />;
    }
  };

  const getTransactionBadge = (type) => {
    const badges = {
      stock_in: { label: 'รับเข้า', variant: 'success' },
      transfer: { label: 'โอนย้าย', variant: 'default' },
      adjustment: { label: 'ปรับยอด', variant: 'warning' }
    };
    return badges[type] || { label: type, variant: 'default' };
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold">รายการเคลื่อนไหวสต็อก</h1>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full sm:w-auto">
              <Plus className="h-4 w-4 mr-2" />
              เพิ่มรายการ
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>เพิ่มรายการเคลื่อนไหวสต็อก</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="type">ประเภทรายการ</Label>
                <Select value={newTransaction.type} onValueChange={(value) => 
                  setNewTransaction({...newTransaction, type: value})
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="stock_in">รับสินค้าเข้า</SelectItem>
                    <SelectItem value="transfer">โอนย้ายสินค้า</SelectItem>
                    <SelectItem value="adjustment">ปรับยอดสต็อก</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="product_id">สินค้า</Label>
                <Select value={newTransaction.product_id} onValueChange={(value) => 
                  setNewTransaction({...newTransaction, product_id: value})
                }>
                  <SelectTrigger>
                    <SelectValue placeholder="เลือกสินค้า" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id.toString()}>
                        {product.name} ({product.sku})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {newTransaction.type === 'stock_in' && (
                <div>
                  <Label htmlFor="to_location_id">สาขาปลายทาง</Label>
                  <Select value={newTransaction.to_location_id} onValueChange={(value) => 
                    setNewTransaction({...newTransaction, to_location_id: value})
                  }>
                    <SelectTrigger>
                      <SelectValue placeholder="เลือกสาขา" />
                    </SelectTrigger>
                    <SelectContent>
                      {locations.map((location) => (
                        <SelectItem key={location.id} value={location.id.toString()}>
                          {location.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {newTransaction.type === 'transfer' && (
                <>
                  <div>
                    <Label htmlFor="from_location_id">สาขาต้นทาง</Label>
                    <Select value={newTransaction.from_location_id} onValueChange={(value) => 
                      setNewTransaction({...newTransaction, from_location_id: value})
                    }>
                      <SelectTrigger>
                        <SelectValue placeholder="เลือกสาขา" />
                      </SelectTrigger>
                      <SelectContent>
                        {locations.map((location) => (
                          <SelectItem key={location.id} value={location.id.toString()}>
                            {location.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="to_location_id">สาขาปลายทาง</Label>
                    <Select value={newTransaction.to_location_id} onValueChange={(value) => 
                      setNewTransaction({...newTransaction, to_location_id: value})
                    }>
                      <SelectTrigger>
                        <SelectValue placeholder="เลือกสาขา" />
                      </SelectTrigger>
                      <SelectContent>
                        {locations.filter(loc => loc.id.toString() !== newTransaction.from_location_id).map((location) => (
                          <SelectItem key={location.id} value={location.id.toString()}>
                            {location.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              {newTransaction.type === 'stock_in' && (
                <div>
                  <Label htmlFor="supplier_id">ผู้ขาย</Label>
                  <Select value={newTransaction.supplier_id} onValueChange={(value) => 
                    setNewTransaction({...newTransaction, supplier_id: value})
                  }>
                    <SelectTrigger>
                      <SelectValue placeholder="เลือกผู้ขาย" />
                    </SelectTrigger>
                    <SelectContent>
                      {suppliers.map((supplier) => (
                        <SelectItem key={supplier.id} value={supplier.id.toString()}>
                          {supplier.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div>
                <Label htmlFor="quantity">จำนวน</Label>
                <Input
                  type="number"
                  value={newTransaction.quantity}
                  onChange={(e) => setNewTransaction({...newTransaction, quantity: e.target.value})}
                  placeholder="จำนวน"
                  required
                />
              </div>

              <div>
                <Label htmlFor="notes">หมายเหตุ</Label>
                <Textarea
                  value={newTransaction.notes}
                  onChange={(e) => setNewTransaction({...newTransaction, notes: e.target.value})}
                  placeholder="หมายเหตุ (ถ้ามี)"
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit" className="flex-1">บันทึก</Button>
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  ยกเลิก
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {transactions.map((transaction) => {
            const badge = getTransactionBadge(transaction.type);
            
            return (
              <Card key={transaction.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        {getTransactionIcon(transaction.type)}
                        <h3 className="font-semibold">{transaction.product.name}</h3>
                        <Badge variant={badge.variant}>{badge.label}</Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">SKU:</span> {transaction.product.sku}
                        </div>
                        <div>
                          <span className="font-medium">จำนวน:</span> {transaction.quantity} {transaction.product.unit}
                        </div>
                        <div>
                          <span className="font-medium">วันที่:</span> {new Date(transaction.created_at).toLocaleDateString('th-TH')}
                        </div>
                      </div>
                      
                      {transaction.type === 'transfer' && (
                        <div className="text-sm text-gray-600">
                          <span className="font-medium">โอนจาก:</span> {transaction.from_location?.name} 
                          <span className="mx-2">→</span>
                          <span className="font-medium">ไปยัง:</span> {transaction.to_location?.name}
                        </div>
                      )}
                      
                      {transaction.type === 'stock_in' && (
                        <div className="text-sm text-gray-600">
                          <span className="font-medium">รับเข้าที่:</span> {transaction.to_location?.name}
                          {transaction.supplier && (
                            <>
                              <span className="mx-2">•</span>
                              <span className="font-medium">ผู้ขาย:</span> {transaction.supplier.name}
                            </>
                          )}
                        </div>
                      )}
                      
                      {transaction.notes && (
                        <div className="text-sm text-gray-600">
                          <span className="font-medium">หมายเหตุ:</span> {transaction.notes}
                        </div>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <div className="text-lg font-bold text-primary">
                        {transaction.quantity > 0 ? '+' : ''}{transaction.quantity}
                      </div>
                      <div className="text-sm text-gray-500">{transaction.product.unit}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
          
          {transactions.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center">
                <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">ไม่มีรายการเคลื่อนไหว</h3>
                <p className="text-gray-500">ยังไม่มีรายการเคลื่อนไหวสต็อกในระบบ</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default StockTransactions;

