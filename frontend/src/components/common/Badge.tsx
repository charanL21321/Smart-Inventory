import React from 'react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
}) => {
  const variantStyles: Record<BadgeVariant, { bg: string; text: string; border: string }> = {
    success: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
    warning: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
    danger: { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' },
    info: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
    neutral: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-200' },
    primary: { bg: 'bg-indigo-50', text: 'text-indigo-600', border: 'border-indigo-200' },
  };

  const style = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${style.bg} ${style.text} ${style.border} ${className}`}
    >
      {children}
    </span>
  );
};
