import React, { useEffect, useState } from 'react';
import { salesApi } from '../api/sales';
import { productsApi } from '../api/products';
import { Sale, Product, SaleCreate } from '../types';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Modal } from '../components/common/Modal';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { ShoppingCart, Plus, Search, DollarSign } from 'lucide-react';

export const Sales: React.FC = () => {
  const [sales, setSales] = useState<Sale[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [searchReference, setSearchReference] = useState<string>('');

  // Record Sale Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [formProductId, setFormProductId] = useState<number | ''>('');
  const [formQuantity, setFormQuantity] = useState<number>(1);
  const [formUnitPrice, setFormUnitPrice] = useState<string>('');
  const [formReference, setFormReference] = useState<string>('');

  const loadSalesData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [salesData, pData] = await Promise.all([
        salesApi.getAll({
          product_id: selectedProduct ? Number(selectedProduct) : undefined,
          reference: searchReference || undefined,
        }),
        productsApi.getAll({ is_active: true }),
      ]);
      setSales(salesData);
      setProducts(pData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load sales history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSalesData();
  }, [selectedProduct]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadSalesData();
  };

  const openRecordModal = () => {
    const firstProduct = products[0];
    setFormProductId(firstProduct?.id || '');
    setFormQuantity(1);
    setFormUnitPrice(firstProduct ? String(firstProduct.price) : '');
    setFormReference('');
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleProductSelect = (id: number) => {
    setFormProductId(id);
    const prod = products.find((p) => p.id === id);
    if (prod) {
      setFormUnitPrice(String(prod.price));
    }
  };

  const handleRecordSale = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formProductId) {
      setFormError('Please select a product.');
      return;
    }
    if (formQuantity <= 0) {
      setFormError('Quantity must be greater than 0.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      const payload: SaleCreate = {
        product_id: Number(formProductId),
        quantity: Number(formQuantity),
        unit_price: formUnitPrice ? Number(formUnitPrice) : undefined,
        reference: formReference || undefined,
      };
      await salesApi.create(payload);
      setIsModalOpen(false);
      loadSalesData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to record sale. Insufficient stock or invalid data.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Sales Transactions</h2>
          <p className="text-sm text-slate-500">
            Record customer sales and automatically trigger inventory stock dispatch.
          </p>
        </div>
        <Button onClick={openRecordModal} icon={<Plus className="h-4 w-4" />}>
          Record Sale
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="card p-4">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Select
              options={products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
              placeholder="All Products"
              value={selectedProduct}
              onChange={(e) => setSelectedProduct(e.target.value)}
            />
          </div>
          <div>
            <Input
              placeholder="Filter by reference (e.g. INV-1002)..."
              value={searchReference}
              onChange={(e) => setSearchReference(e.target.value)}
            />
          </div>
          <div>
            <Button type="submit" variant="secondary" icon={<Search className="h-4 w-4" />}>
              Filter
            </Button>
          </div>
        </form>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadSalesData} />}

      {loading ? (
        <Spinner size="lg" message="Loading sales records..." className="py-12" />
      ) : sales.length === 0 ? (
        <EmptyState
          title="No sales found"
          description="No sales transaction history recorded yet."
          icon={<ShoppingCart className="h-10 w-10" />}
          actionLabel="Record First Sale"
          onAction={openRecordModal}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Date & Time</th>
                <th>Product</th>
                <th>Quantity Sold</th>
                <th>Unit Price</th>
                <th>Total Revenue</th>
                <th>Reference</th>
                <th>Sold By</th>
              </tr>
            </thead>
            <tbody>
              {sales.map((sale) => (
                <tr key={sale.id}>
                  <td className="text-xs text-slate-500 whitespace-nowrap">
                    {new Date(sale.created_at).toLocaleString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td className="font-semibold text-slate-900">
                    {sale.product?.name || `Product #${sale.product_id}`}
                    <div className="text-xs text-slate-400 font-normal">{sale.product?.sku}</div>
                  </td>
                  <td className="font-bold text-slate-800">{sale.quantity}</td>
                  <td>${Number(sale.unit_price).toFixed(2)}</td>
                  <td className="font-bold text-emerald-700">
                    ${Number(sale.total_amount).toFixed(2)}
                  </td>
                  <td className="font-mono text-xs text-slate-600">{sale.reference || '—'}</td>
                  <td className="text-xs text-slate-500">#{sale.sold_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Record Sale Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Record New Business Sale"
      >
        {formError && <ErrorAlert message={formError} className="mb-4" />}
        <form onSubmit={handleRecordSale} className="space-y-4">
          <Select
            label="Select Product"
            required
            options={products.map((p) => ({
              value: p.id,
              label: `${p.name} ($${Number(p.price).toFixed(2)})`,
            }))}
            value={formProductId}
            onChange={(e) => handleProductSelect(Number(e.target.value))}
            disabled={submitting}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Quantity to Sell"
              type="number"
              min="1"
              required
              value={formQuantity}
              onChange={(e) => setFormQuantity(Number(e.target.value))}
              disabled={submitting}
            />
            <Input
              label="Unit Price ($)"
              type="number"
              step="0.01"
              min="0"
              value={formUnitPrice}
              onChange={(e) => setFormUnitPrice(e.target.value)}
              placeholder="Leave blank for catalog price"
              disabled={submitting}
            />
          </div>

          <Input
            label="Invoice / Order Reference (Optional)"
            value={formReference}
            onChange={(e) => setFormReference(e.target.value)}
            placeholder="e.g. POS-2026-904"
            disabled={submitting}
          />

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
            <strong>Note:</strong> Recording this sale will immediately verify available stock,
            deduct the quantity, and create an immutable <code>STOCK_OUT</code> transaction.
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={submitting}>
              Confirm Sale
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
