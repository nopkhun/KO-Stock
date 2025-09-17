import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Search, Filter, Package, AlertTriangle } from 'lucide-react';
import axios from 'axios';

const Inventory = () => {
  const [inventory, setInventory] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInventory();
    fetchLocations();
  }, [selectedLocation]);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const params = selectedLocation !== 'all' ? { location_id: selectedLocation } : {};
      const response = await axios.get('/api/inventory', { params });
      setInventory(response.data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setLoading(false);
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

  const filteredInventory = inventory.filter(item =>
    item.product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.product.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.product.brand.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStockStatus = (quantity, reorderPoint) => {
    if (quantity === 0) return { status: 'out-of-stock', color: 'destructive' };
    if (quantity <= reorderPoint) return { status: 'low-stock', color: 'warning' };
    return { status: 'in-stock', color: 'success' };
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold">สต็อกสินค้า</h1>
        
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="ค้นหาสินค้า..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-full sm:w-64"
            />
          </div>
          
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-full sm:w-48">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="เลือกสาขา" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">ทุกสาขา</SelectItem>
              {locations.map((location) => (
                <SelectItem key={location.id} value={location.id.toString()}>
                  {location.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredInventory.map((item) => {
            const stockStatus = getStockStatus(item.quantity, item.product.reorder_point);
            
            return (
              <Card key={`${item.product.id}-${item.location.id}`} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Package className="h-5 w-5 text-primary" />
                        <h3 className="font-semibold text-lg">{item.product.name}</h3>
                      </div>
                      
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">SKU:</span> {item.product.sku}
                        </div>
                        <div>
                          <span className="font-medium">ยี่ห้อ:</span> {item.product.brand.name}
                        </div>
                        <div>
                          <span className="font-medium">หมวดหมู่:</span> {item.product.category}
                        </div>
                        <div>
                          <span className="font-medium">สาขา:</span> {item.location.name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{item.quantity}</div>
                        <div className="text-sm text-gray-500">{item.product.unit}</div>
                      </div>
                      
                      <Badge 
                        variant={stockStatus.color}
                        className="flex items-center gap-1"
                      >
                        {stockStatus.status === 'out-of-stock' && <AlertTriangle className="h-3 w-3" />}
                        {stockStatus.status === 'low-stock' && <AlertTriangle className="h-3 w-3" />}
                        {stockStatus.status === 'out-of-stock' ? 'หมดสต็อก' : 
                         stockStatus.status === 'low-stock' ? 'สต็อกต่ำ' : 'มีสต็อก'}
                      </Badge>
                    </div>
                  </div>
                  
                  {item.quantity <= item.product.reorder_point && (
                    <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                      <div className="flex items-center gap-2 text-yellow-800 text-sm">
                        <AlertTriangle className="h-4 w-4" />
                        <span>จุดสั่งซื้อขั้นต่ำ: {item.product.reorder_point} {item.product.unit}</span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
          
          {filteredInventory.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center">
                <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">ไม่พบข้อมูลสต็อก</h3>
                <p className="text-gray-500">ไม่มีสินค้าที่ตรงกับเงื่อนไขการค้นหา</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default Inventory;

