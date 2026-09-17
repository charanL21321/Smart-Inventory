import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { StatusBadge } from '../common/StatusBadge';
import { LogOut, User as UserIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-sm sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Smart Operations Portal
        </span>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <Link
            to="/profile"
            className="flex items-center gap-3 p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-inherit no-underline"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-semibold text-xs border border-indigo-200">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-semibold text-slate-800 leading-tight">
                {user.full_name || user.username}
              </div>
              <div className="text-[11px] text-slate-500">{user.email}</div>
            </div>
            <StatusBadge status={user.role} />
          </Link>
        )}

        <div className="h-5 w-px bg-slate-200" />

        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-rose-600 p-2 rounded-lg hover:bg-rose-50 transition-colors cursor-pointer border-0 bg-transparent"
          title="Sign Out"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden md:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
};
