import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Calendar, Save, Calculator, TrendingDown } from 'lucide-react';
import axios from 'axios';

const DailyCount = () => {
  const [dailyCounts, setDailyCounts] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [countData, setCountData] = useState([]);

  useEffect(() => {
    fetchLocations();
  }, []);

  useEffect(() => {
    if (selectedLocation) {
      fetchDailyCounts();
      fetchInventoryForLocation();
    }
  }, [selectedLocation, selectedDate]);

  const fetchLocations = async () => {
    try {
      const response = await axios.get('/api/locations');
      const storeLocations = response.data.filter(loc => loc.location_type === 'store');
      setLocations(storeLocations);
      if (storeLocations.length > 0) {
        setSelectedLocation(storeLocations[0].id.toString());
      }
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchDailyCounts = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/daily-counts', {
        params: {
          location_id: selectedLocation,
          date: selectedDate
        }
      });
      setDailyCounts(response.data);
    } catch (error) {
      console.error('Error fetching daily counts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInventoryForLocation = async () => {
    try {
      const response = await axios.get('/api/inventory', {
        params: { location_id: selectedLocation }
      });
      setInventory(response.data);
      
      // Initialize count data with current inventory
      const initialCountData = response.data.map(item => ({
        product_id: item.product.id,
        product_name: item.product.name,
        product_sku: item.product.sku,
        current_quantity: item.quantity,
        counted_quantity: item.quantity,
        unit: item.product.unit
      }));
      setCountData(initialCountData);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    }
  };

  const handleCountChange = (productId, countedQuantity) => {
    setCountData(prev => prev.map(item => 
      item.product_id === productId 
        ? { ...item, counted_quantity: parseInt(countedQuantity) || 0 }
        : item
    ));
  };

  const handleSubmitCount = async () => {
    try {
      const countPayload = {
        location_id: parseInt(selectedLocation),
        count_date: selectedDate,
        items: countData.map(item => ({
          product_id: item.product_id,
          counted_quantity: item.counted_quantity
        }))
      };

      await axios.post('/api/daily-counts', countPayload);
      setIsDialogOpen(false);
      fetchDailyCounts();
    } catch (error) {
      console.error('Error submitting daily count:', error);
    }
  };

  const calculateUsage = (currentQty, countedQty) => {
    return currentQty - countedQty;
  };

  const getTodayCount = () => {
    const today = new Date().toISOString().split('T')[0];
    return dailyCounts.find(count => count.count_date === today);
  };

  const todayCount = getTodayCount();

  return (
    <div className="p-4 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold">นับสต็อกรายวัน</h1>
        
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-full sm:w-48">
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
          
          <Input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-full sm:w-auto"
          />
          
          {!todayCount && selectedDate === new Date().toISOString().split('T')[0] && (
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button className="w-full sm:w-auto">
                  <Calculator className="h-4 w-4 mr-2" />
                  นับสต็อกวันนี้
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>นับสต็อกประจำวัน - {new Date(selectedDate).toLocaleDateString('th-TH')}</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div className="grid gap-4">
                    {countData.map((item) => (
                      <Card key={item.product_id} className="p-4">
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                          <div className="flex-1">
                            <h3 className="font-semibold">{item.product_name}</h3>
                            <p className="text-sm text-gray-600">SKU: {item.product_sku}</p>
                            <p className="text-sm text-gray-600">สต็อกปัจจุบัน: {item.current_quantity} {item.unit}</p>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Label htmlFor={`count-${item.product_id}`} className="text-sm">
                              นับได้:
                            </Label>
                            <Input
                              id={`count-${item.product_id}`}
                              type="number"
                              value={item.counted_quantity}
                              onChange={(e) => handleCountChange(item.product_id, e.target.value)}
                              className="w-20"
                              min="0"
                            />
                            <span className="text-sm text-gray-600">{item.unit}</span>
                          </div>
                          
                          <div className="text-right">
                            <div className="text-sm text-gray-600">ใช้ไป:</div>
                            <div className={`font-bold ${calculateUsage(item.current_quantity, item.counted_quantity) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                              {calculateUsage(item.current_quantity, item.counted_quantity)} {item.unit}
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                  
                  <div className="flex gap-2">
                    <Button onClick={handleSubmitCount} className="flex-1">
                      <Save className="h-4 w-4 mr-2" />
                      บันทึกการนับสต็อก
                    </Button>
                    <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                      ยกเลิก
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {dailyCounts.length > 0 ? (
            dailyCounts.map((count) => (
              <Card key={count.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    การนับสต็อกวันที่ {new Date(count.count_date).toLocaleDateString('th-TH')}
                    <Badge variant="success">เสร็จสิ้น</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {count.items.map((item) => (
                      <div key={item.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <h4 className="font-medium">{item.product.name}</h4>
                          <p className="text-sm text-gray-600">SKU: {item.product.sku}</p>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div className="text-center">
                            <div className="text-gray-600">สต็อกเริ่มต้น</div>
                            <div className="font-semibold">{item.opening_quantity} {item.product.unit}</div>
                          </div>
                          <div className="text-center">
                            <div className="text-gray-600">นับได้</div>
                            <div className="font-semibold">{item.counted_quantity} {item.product.unit}</div>
                          </div>
                          <div className="text-center">
                            <div className="text-gray-600">ใช้ไป</div>
                            <div className={`font-semibold flex items-center justify-center gap-1 ${item.usage_quantity > 0 ? 'text-red-600' : 'text-green-600'}`}>
                              {item.usage_quantity > 0 && <TrendingDown className="h-3 w-3" />}
                              {item.usage_quantity} {item.product.unit}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-sm text-blue-800">
                      <strong>สรุป:</strong> นับสต็อกเสร็จสิ้นเมื่อ {new Date(count.created_at).toLocaleString('th-TH')}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">ไม่มีข้อมูลการนับสต็อก</h3>
                <p className="text-gray-500">ยังไม่มีการนับสต็อกในวันที่เลือก</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default DailyCount;

