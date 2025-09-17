import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FileText, Download, Calendar, TrendingUp, Package, AlertTriangle } from 'lucide-react';
import axios from 'axios';

const Reports = () => {
  const [locations, setLocations] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const [reportParams, setReportParams] = useState({
    type: 'inventory_summary',
    location_id: 'all',
    supplier_id: 'all',
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchLocations();
    fetchSuppliers();
  }, []);

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

  const generateReport = async () => {
    try {
      setLoading(true);
      const params = { ...reportParams };
      if (params.location_id === 'all') delete params.location_id;
      if (params.supplier_id === 'all') delete params.supplier_id;
      
      const response = await axios.get(`/api/reports/${reportParams.type}`, { params });
      setReportData(response.data);
    } catch (error) {
      console.error('Error generating report:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format = 'pdf') => {
    try {
      const params = { ...reportParams, format };
      if (params.location_id === 'all') delete params.location_id;
      if (params.supplier_id === 'all') delete params.supplier_id;
      
      const response = await axios.get(`/api/reports/${reportParams.type}/export`, {
        params,
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportParams.type}_${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  const reportTypes = {
    inventory_summary: 'รายงานสรุปสต็อกคงเหลือ',
    stock_movement: 'รายงานความเคลื่อนไหวสต็อก',
    usage_summary: 'รายงานสรุปการใช้งานสินค้า',
    purchase_suggestion: 'รายการแนะนำสั่งซื้อ',
    low_stock: 'รายงานสินค้าใกล้หมด'
  };

  const renderInventorySummary = () => {
    if (!reportData?.inventory) return null;
    
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Package className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold">{reportData.summary.total_products}</div>
              <div className="text-sm text-gray-600">รายการสินค้าทั้งหมด</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <TrendingUp className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <div className="text-2xl font-bold">{reportData.summary.total_value?.toLocaleString()}</div>
              <div className="text-sm text-gray-600">มูลค่าสต็อกรวม (บาท)</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-2" />
              <div className="text-2xl font-bold">{reportData.summary.low_stock_items}</div>
              <div className="text-sm text-gray-600">สินค้าใกล้หมด</div>
            </CardContent>
          </Card>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>รายละเอียดสต็อกสินค้า</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {reportData.inventory.map((item, index) => (
                <div key={index} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 p-3 border rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium">{item.product_name}</h4>
                    <p className="text-sm text-gray-600">SKU: {item.sku} • {item.location_name}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-semibold">{item.quantity} {item.unit}</div>
                      <div className="text-sm text-gray-600">คงเหลือ</div>
                    </div>
                    {item.quantity <= item.reorder_point && (
                      <Badge variant="destructive">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        ใกล้หมด
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderPurchaseSuggestion = () => {
    if (!reportData?.suggestions) return null;
    
    return (
      <div className="space-y-4">
        {Object.entries(reportData.suggestions).map(([supplierName, items]) => (
          <Card key={supplierName}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                {supplierName}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {items.map((item, index) => (
                  <div key={index} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <h4 className="font-medium">{item.product_name}</h4>
                      <p className="text-sm text-gray-600">SKU: {item.sku}</p>
                      <p className="text-sm text-gray-600">คงเหลือ: {item.current_stock} {item.unit}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-red-600">{item.suggested_quantity} {item.unit}</div>
                      <div className="text-sm text-gray-600">แนะนำสั่งซื้อ</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  const renderReportContent = () => {
    if (!reportData) return null;
    
    switch (reportParams.type) {
      case 'inventory_summary':
        return renderInventorySummary();
      case 'purchase_suggestion':
        return renderPurchaseSuggestion();
      default:
        return (
          <Card>
            <CardContent className="p-8 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">รายงานพร้อมแล้ว</h3>
              <p className="text-gray-500">ข้อมูลรายงานได้ถูกสร้างเรียบร้อยแล้ว</p>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className="p-4 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold">รายงาน</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>สร้างรายงาน</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="report-type">ประเภทรายงาน</Label>
              <Select value={reportParams.type} onValueChange={(value) => 
                setReportParams({...reportParams, type: value})
              }>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(reportTypes).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="location">สาขา</Label>
              <Select value={reportParams.location_id} onValueChange={(value) => 
                setReportParams({...reportParams, location_id: value})
              }>
                <SelectTrigger>
                  <SelectValue />
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

            {reportParams.type === 'purchase_suggestion' && (
              <div>
                <Label htmlFor="supplier">ผู้ขาย</Label>
                <Select value={reportParams.supplier_id} onValueChange={(value) => 
                  setReportParams({...reportParams, supplier_id: value})
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">ทุกผู้ขาย</SelectItem>
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
              <Label htmlFor="start-date">วันที่เริ่มต้น</Label>
              <Input
                type="date"
                value={reportParams.start_date}
                onChange={(e) => setReportParams({...reportParams, start_date: e.target.value})}
              />
            </div>

            <div>
              <Label htmlFor="end-date">วันที่สิ้นสุด</Label>
              <Input
                type="date"
                value={reportParams.end_date}
                onChange={(e) => setReportParams({...reportParams, end_date: e.target.value})}
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Button onClick={generateReport} disabled={loading} className="flex-1 sm:flex-none">
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <FileText className="h-4 w-4 mr-2" />
              )}
              สร้างรายงาน
            </Button>
            
            {reportData && (
              <Button variant="outline" onClick={() => exportReport('pdf')}>
                <Download className="h-4 w-4 mr-2" />
                ส่งออก PDF
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {reportData && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="h-5 w-5" />
            <h2 className="text-xl font-semibold">{reportTypes[reportParams.type]}</h2>
            <Badge variant="success">สร้างเสร็จแล้ว</Badge>
          </div>
          {renderReportContent()}
        </div>
      )}
    </div>
  );
};

export default Reports;

