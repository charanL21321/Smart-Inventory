import React, { useEffect, useState } from 'react';
import { productsApi } from '../api/products';
import { categoriesApi } from '../api/categories';
import { suppliersApi } from '../api/suppliers';
import { Product, Category, Supplier, ProductCreate, ProductUpdate } from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { Modal } from '../components/common/Modal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Badge } from '../components/common/Badge';
import { Plus, Search, Edit2, Trash2, Package } from 'lucide-react';

export const Products: React.FC = () => {
  const { hasRole } = useAuth();
  const canManage = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedSupplier, setSelectedSupplier] = useState<string>('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [deleteProductTarget, setDeleteProductTarget] = useState<Product | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [formSku, setFormSku] = useState('');
  const [formName, setFormName] = useState('');
  const [formCategoryId, setFormCategoryId] = useState<number | ''>('');
  const [formSupplierId, setFormSupplierId] = useState<number | ''>('');
  const [formPrice, setFormPrice] = useState<number>(0);
  const [formReorderPoint, setFormReorderPoint] = useState<number>(10);
  const [formSafetyStock, setFormSafetyStock] = useState<number>(5);
  const [formTargetStock, setFormTargetStock] = useState<number>(50);
  const [formDescription, setFormDescription] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [pData, cData, sData] = await Promise.all([
        productsApi.getAll({
          search: search || undefined,
          category_id: selectedCategory ? Number(selectedCategory) : undefined,
          supplier_id: selectedSupplier ? Number(selectedSupplier) : undefined,
        }),
        categoriesApi.getAll(true),
        suppliersApi.getAll(true),
      ]);
      setProducts(pData);
      setCategories(cData);
      setSuppliers(sData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load products catalogue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCategory, selectedSupplier]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const openCreateModal = () => {
    setEditingProduct(null);
    setFormSku('');
    setFormName('');
    setFormCategoryId(categories[0]?.id || '');
    setFormSupplierId(suppliers[0]?.id || '');
    setFormPrice(0);
    setFormReorderPoint(10);
    setFormSafetyStock(5);
    setFormTargetStock(50);
    setFormDescription('');
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (p: Product) => {
    setEditingProduct(p);
    setFormSku(p.sku);
    setFormName(p.name);
    setFormCategoryId(p.category_id);
    setFormSupplierId(p.supplier_id);
    setFormPrice(p.price);
    setFormReorderPoint(p.reorder_point);
    setFormSafetyStock(p.safety_stock);
    setFormTargetStock(p.target_stock);
    setFormDescription(p.description || '');
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formSku.trim() || !formName.trim() || !formCategoryId || !formSupplierId) {
      setFormError('Please fill in all mandatory fields.');
      return;
    }
    if (formTargetStock <= 0) {
      setFormError('Target stock must be strictly greater than 0.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);

      if (editingProduct) {
        const updatePayload: ProductUpdate = {
          sku: formSku,
          name: formName,
          category_id: Number(formCategoryId),
          supplier_id: Number(formSupplierId),
          price: Number(formPrice),
          reorder_point: Number(formReorderPoint),
          safety_stock: Number(formSafetyStock),
          target_stock: Number(formTargetStock),
          description: formDescription || undefined,
        };
        await productsApi.update(editingProduct.id, updatePayload);
      } else {
        const createPayload: ProductCreate = {
          sku: formSku,
          name: formName,
          category_id: Number(formCategoryId),
          supplier_id: Number(formSupplierId),
          price: Number(formPrice),
          reorder_point: Number(formReorderPoint),
          safety_stock: Number(formSafetyStock),
          target_stock: Number(formTargetStock),
          description: formDescription || undefined,
        };
        await productsApi.create(createPayload);
      }

      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save product.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!deleteProductTarget) return;
    try {
      setSubmitting(true);
      await productsApi.delete(deleteProductTarget.id);
      setDeleteProductTarget(null);
      loadData();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete product.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Products Catalog</h2>
          <p className="text-sm text-slate-500">
            Define SKUs, target inventory parameters, and supplier links.
          </p>
        </div>
        {canManage && (
          <Button onClick={openCreateModal} icon={<Plus className="h-4 w-4" />}>
            New Product
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="card p-4">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <Input
              placeholder="Search products by name or SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div>
            <Select
              options={categories.map((c) => ({ value: c.id, label: c.name }))}
              placeholder="All Categories"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Select
              options={suppliers.map((s) => ({ value: s.id, label: s.name }))}
              placeholder="All Suppliers"
              value={selectedSupplier}
              onChange={(e) => setSelectedSupplier(e.target.value)}
            />
            <Button type="submit" variant="secondary" icon={<Search className="h-4 w-4" />} />
          </div>
        </form>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadData} />}

      {/* Table */}
      {loading ? (
        <Spinner size="lg" message="Loading product catalog..." className="py-12" />
      ) : products.length === 0 ? (
        <EmptyState
          title="No products found"
          description="No products match your current search or filter criteria."
          icon={<Package className="h-10 w-10" />}
          actionLabel={canManage ? 'Create First Product' : undefined}
          onAction={openCreateModal}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Category</th>
                <th>Supplier</th>
                <th>Price</th>
                <th>ROP / Safety / Target</th>
                <th>Status</th>
                {canManage && <th className="text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id}>
                  <td className="font-mono text-xs font-semibold text-slate-800">{p.sku}</td>
                  <td className="font-medium text-slate-900">{p.name}</td>
                  <td>{p.category?.name || `Cat #${p.category_id}`}</td>
                  <td>{p.supplier?.name || `Sup #${p.supplier_id}`}</td>
                  <td>${Number(p.price).toFixed(2)}</td>
                  <td className="text-xs text-slate-500">
                    <span className="font-semibold text-slate-700">{p.reorder_point}</span> /{' '}
                    <span>{p.safety_stock}</span> /{' '}
                    <span className="text-indigo-600 font-semibold">{p.target_stock}</span>
                  </td>
                  <td>
                    <Badge variant={p.is_active ? 'success' : 'neutral'}>
                      {p.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  {canManage && (
                    <td className="text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => openEditModal(p)}
                          className="p-1 text-slate-500 hover:text-indigo-600 rounded transition-colors"
                          title="Edit Product"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteProductTarget(p)}
                          className="p-1 text-slate-500 hover:text-rose-600 rounded transition-colors"
                          title="Delete Product"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingProduct ? 'Edit Product' : 'Create New Product'}
        maxWidth="lg"
      >
        {formError && <ErrorAlert message={formError} className="mb-4" />}
        <form onSubmit={handleSaveProduct} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="SKU Code"
              required
              value={formSku}
              onChange={(e) => setFormSku(e.target.value)}
              placeholder="e.g. ELEC-001"
              disabled={submitting}
            />
            <Input
              label="Product Name"
              required
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder="e.g. Wireless Barcode Scanner"
              disabled={submitting}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Category"
              required
              options={categories.map((c) => ({ value: c.id, label: c.name }))}
              value={formCategoryId}
              onChange={(e) => setFormCategoryId(Number(e.target.value))}
              disabled={submitting}
            />
            <Select
              label="Supplier"
              required
              options={suppliers.map((s) => ({ value: s.id, label: s.name }))}
              value={formSupplierId}
              onChange={(e) => setFormSupplierId(Number(e.target.value))}
              disabled={submitting}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Input
              label="Price ($)"
              type="number"
              step="0.01"
              min="0"
              required
              value={formPrice}
              onChange={(e) => setFormPrice(Number(e.target.value))}
              disabled={submitting}
            />
            <Input
              label="Reorder Point"
              type="number"
              min="0"
              required
              value={formReorderPoint}
              onChange={(e) => setFormReorderPoint(Number(e.target.value))}
              disabled={submitting}
            />
            <Input
              label="Safety Stock"
              type="number"
              min="0"
              required
              value={formSafetyStock}
              onChange={(e) => setFormSafetyStock(Number(e.target.value))}
              disabled={submitting}
            />
            <Input
              label="Target Stock (>0)"
              type="number"
              min="1"
              required
              value={formTargetStock}
              onChange={(e) => setFormTargetStock(Number(e.target.value))}
              disabled={submitting}
            />
          </div>

          <div>
            <label className="label">Description (Optional)</label>
            <textarea
              className="textarea"
              rows={3}
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              placeholder="Product notes, specifications..."
              disabled={submitting}
            />
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
              {editingProduct ? 'Update Product' : 'Create Product'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteProductTarget}
        onClose={() => setDeleteProductTarget(null)}
        onConfirm={handleDeleteProduct}
        title="Delete Product"
        message={`Are you sure you want to delete "${deleteProductTarget?.name}"? If there is existing stock or order history, it may be deactivated instead.`}
        confirmLabel="Delete"
        variant="danger"
        loading={submitting}
      />
    </div>
  );
};
