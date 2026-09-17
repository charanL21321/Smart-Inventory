import React, { useEffect, useState } from 'react';
import { categoriesApi } from '../api/categories';
import { Category, CategoryCreate, CategoryUpdate } from '../types';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Modal } from '../components/common/Modal';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Spinner } from '../components/common/Spinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Badge } from '../components/common/Badge';
import { Plus, Search, Edit2, Trash2, Tags } from 'lucide-react';

export const Categories: React.FC = () => {
  const { hasRole } = useAuth();
  const canManage = hasRole('ADMIN', 'INVENTORY_MANAGER');

  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [formName, setFormName] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formIsActive, setFormIsActive] = useState(true);

  const loadCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await categoriesApi.getAll(undefined, search || undefined);
      setCategories(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load categories.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCategories();
  };

  const openCreateModal = () => {
    setEditingCategory(null);
    setFormName('');
    setFormDescription('');
    setFormIsActive(true);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (cat: Category) => {
    setEditingCategory(cat);
    setFormName(cat.name);
    setFormDescription(cat.description || '');
    setFormIsActive(cat.is_active);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) {
      setFormError('Category name is required.');
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);
      if (editingCategory) {
        const updatePayload: CategoryUpdate = {
          name: formName,
          description: formDescription || undefined,
          is_active: formIsActive,
        };
        await categoriesApi.update(editingCategory.id, updatePayload);
      } else {
        const createPayload: CategoryCreate = {
          name: formName,
          description: formDescription || undefined,
        };
        await categoriesApi.create(createPayload);
      }
      setIsModalOpen(false);
      loadCategories();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save category.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      setSubmitting(true);
      await categoriesApi.delete(deleteTarget.id);
      setDeleteTarget(null);
      loadCategories();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete category.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Product Categories</h2>
          <p className="text-sm text-slate-500">Group catalog items for structured stock operations.</p>
        </div>
        {canManage && (
          <Button onClick={openCreateModal} icon={<Plus className="h-4 w-4" />}>
            New Category
          </Button>
        )}
      </div>

      <div className="card p-4">
        <form onSubmit={handleSearchSubmit} className="flex gap-3">
          <Input
            placeholder="Search categories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button type="submit" variant="secondary" icon={<Search className="h-4 w-4" />}>
            Search
          </Button>
        </form>
      </div>

      {error && <ErrorAlert message={error} onRetry={loadCategories} />}

      {loading ? (
        <Spinner size="lg" message="Loading categories..." className="py-12" />
      ) : categories.length === 0 ? (
        <EmptyState
          title="No categories found"
          description="No categories match your search query."
          icon={<Tags className="h-10 w-10" />}
          actionLabel={canManage ? 'Create Category' : undefined}
          onAction={openCreateModal}
        />
      ) : (
        <div className="table-container shadow-sm">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Category Name</th>
                <th>Description</th>
                <th>Status</th>
                {canManage && <th className="text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.id}>
                  <td className="text-xs text-slate-400">#{cat.id}</td>
                  <td className="font-semibold text-slate-900">{cat.name}</td>
                  <td className="text-sm text-slate-600">{cat.description || '—'}</td>
                  <td>
                    <Badge variant={cat.is_active ? 'success' : 'neutral'}>
                      {cat.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  {canManage && (
                    <td className="text-right">
                      <div className="inline-flex gap-2">
                        <button
                          onClick={() => openEditModal(cat)}
                          className="p-1 text-slate-500 hover:text-indigo-600 rounded transition-colors"
                          title="Edit Category"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(cat)}
                          className="p-1 text-slate-500 hover:text-rose-600 rounded transition-colors"
                          title="Delete Category"
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

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingCategory ? 'Edit Category' : 'Create New Category'}
      >
        {formError && <ErrorAlert message={formError} className="mb-4" />}
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label="Category Name"
            required
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
            placeholder="e.g. Raw Materials"
            disabled={submitting}
          />
          <div>
            <label className="label">Description (Optional)</label>
            <textarea
              className="textarea"
              rows={3}
              value={formDescription}
              onChange={(e) => setFormDescription(e.target.value)}
              placeholder="Detailed description of category scope..."
              disabled={submitting}
            />
          </div>
          {editingCategory && (
            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formIsActive}
                onChange={(e) => setFormIsActive(e.target.checked)}
                className="h-4 w-4 text-indigo-600 rounded"
              />
              <label htmlFor="is_active" className="text-sm font-medium text-slate-700">
                Active Category
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
              {editingCategory ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Dialog */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Category"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        confirmLabel="Delete"
        variant="danger"
        loading={submitting}
      />
    </div>
  );
};
