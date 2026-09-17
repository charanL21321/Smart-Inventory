import React, { useEffect, useState } from 'react';
import { suppliersApi } from '../api/suppliers';
import { Supplier, SupplierCreate, SupplierUpdate } from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Modal } from '../components/common/Modal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Badge } from '../components/common/Badge';
import { Plus, Search, Edit2, Trash2, Truck } from 'lucide-react';

export const Suppliers: React.FC = () => {
  const { hasRole } = useAuth();
  const canManage = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Supplier | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [formName, setFormName] = useState('');
  const [formContactPerson, setFormContactPerson] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formAddress, setFormAddress] = useState('');
  const [formLeadTime, setFormLeadTime] = useState<number>(7);
  const [formMoq, setFormMoq] = useState<number>(10);
  const [formIsActive, setFormIsActive] = useState(true);

  const loadSuppliers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await suppliersApi.getAll(undefined, search || undefined);
      setSuppliers(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load suppliers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSuppliers();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadSuppliers();
  };

  const openCreateModal = () => {
    setEditingSupplier(null);
    setFormName('');
    setFormContactPerson('');
    setFormEmail('');
    setFormPhone('');
    setFormAddress('');
    setFormLeadTime(7);
    setFormMoq(10);
    setFormIsActive(true);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (s: Supplier) => {
    setEditingSupplier(s);
    setFormName(s.name);
    setFormContactPerson(s.contact_person || '');
    setFormEmail(s.email);
    setFormPhone(s.phone);
    setFormAddress(s.address || '');
    setFormLeadTime(s.lead_time_days);
    setFormMoq(s.minimum_order_quantity);
    setFormIsActive(s.is_active);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formEmail.trim() || !formPhone.trim()) {
      setFormError('Supplier name, email, and phone number are required.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      if (editingSupplier) {
        const updatePayload: SupplierUpdate = {
          name: formName,
          contact_person: formContactPerson || undefined,
          email: formEmail,
          phone: formPhone,
          address: formAddress || undefined,
          lead_time_days: Number(formLeadTime),
          minimum_order_quantity: Number(formMoq),
          is_active: formIsActive,
        };
        await suppliersApi.update(editingSupplier.id, updatePayload);
      } else {
        const createPayload: SupplierCreate = {
          name: formName,
          contact_person: formContactPerson || undefined,
          email: formEmail,
          phone: formPhone,
          address: formAddress || undefined,
          lead_time_days: Number(formLeadTime),
          minimum_order_quantity: Number(formMoq),
        };
        await suppliersApi.create(createPayload);
      }
      setIsModalOpen(false);
      loadSuppliers();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save supplier.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      setSubmitting(true);
      await suppliersApi.delete(deleteTarget.id);
      setDeleteTarget(null);
      loadSuppliers();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete supplier.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Suppliers Directory</h2>
          <p className="text-sm text-slate-500">
            Manage procurement partners, lead time metrics, and minimum order rules.
          </p>
        </div>
        {canManage && (
          <Button onClick={openCreateModal} icon={<Plus className="h-4 w-4" />}>
            New Supplier
          </Button>
        )}
      </div>

      <div className="card p-4">
        <form onSubmit={handleSearchSubmit} className="flex gap-3">
          <Input
            placeholder="Search suppliers by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button type="submit" variant="secondary" icon={<Search className="h-4 w-4" />}>
            Search
          </Button>
        </form>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadSuppliers} />}

      {loading ? (
        <Spinner size="lg" message="Loading suppliers..." className="py-12" />
      ) : suppliers.length === 0 ? (
        <EmptyState
          title="No suppliers found"
          description="No supplier partners found matching your search."
          icon={<Truck className="h-10 w-10" />}
          actionLabel={canManage ? 'Create Supplier' : undefined}
          onAction={openCreateModal}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>Supplier Name</th>
                <th>Contact</th>
                <th>Email & Phone</th>
                <th>Lead Time</th>
                <th>Min Order (MOQ)</th>
                <th>Status</th>
                {canManage && <th className="text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {suppliers.map((s) => (
                <tr key={s.id}>
                  <td className="font-semibold text-slate-900">{s.name}</td>
                  <td>{s.contact_person || '—'}</td>
                  <td className="text-xs">
                    <div className="text-slate-800">{s.email}</div>
                    <div className="text-slate-500">{s.phone}</div>
                  </td>
                  <td>
                    <span className="font-medium">{s.lead_time_days}</span> days
                  </td>
                  <td>
                    <span className="font-medium">{s.minimum_order_quantity}</span> units
                  </td>
                  <td>
                    <Badge variant={s.is_active ? 'success' : 'neutral'}>
                      {s.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  {canManage && (
                    <td className="text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => openEditModal(s)}
                          className="p-1 text-slate-500 hover:text-indigo-600 rounded transition-colors"
                          title="Edit Supplier"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(s)}
                          className="p-1 text-slate-500 hover:text-rose-600 rounded transition-colors"
                          title="Delete Supplier"
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
        title={editingSupplier ? 'Edit Supplier' : 'Create New Supplier'}
        maxWidth="lg"
      >
        {formError && <ErrorAlert message={formError} className="mb-4" />}
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Supplier Company Name"
              required
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder="e.g. Apex Industrial Supplies"
              disabled={submitting}
            />
            <Input
              label="Contact Person"
              value={formContactPerson}
              onChange={(e) => setFormContactPerson(e.target.value)}
              placeholder="e.g. John Doe"
              disabled={submitting}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Email Address"
              type="email"
              required
              value={formEmail}
              onChange={(e) => setFormEmail(e.target.value)}
              placeholder="orders@apexsupplies.com"
              disabled={submitting}
            />
            <Input
              label="Phone Number"
              required
              value={formPhone}
              onChange={(e) => setFormPhone(e.target.value)}
              placeholder="+1-555-0199"
              disabled={submitting}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Lead Time (Days)"
              type="number"
              min="0"
              required
              value={formLeadTime}
              onChange={(e) => setFormLeadTime(Number(e.target.value))}
              disabled={submitting}
            />
            <Input
              label="Minimum Order Quantity (MOQ)"
              type="number"
              min="1"
              required
              value={formMoq}
              onChange={(e) => setFormMoq(Number(e.target.value))}
              disabled={submitting}
            />
          </div>

          <div>
            <label className="label">Mailing Address (Optional)</label>
            <textarea
              className="textarea"
              rows={2}
              value={formAddress}
              onChange={(e) => setFormAddress(e.target.value)}
              placeholder="Physical street address or warehouse location..."
              disabled={submitting}
            />
          </div>

          {editingSupplier && (
            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="supplier_is_active"
                checked={formIsActive}
                onChange={(e) => setFormIsActive(e.target.checked)}
                className="h-4 w-4 text-indigo-600 rounded"
              />
              <label htmlFor="supplier_is_active" className="text-sm font-medium text-slate-700">
                Active Supplier Status
              </label>
            </div>
          )}

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
              {editingSupplier ? 'Update Supplier' : 'Create Supplier'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Supplier"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        confirmLabel="Delete"
        variant="danger"
        loading={submitting}
      />
    </div>
  );
};
