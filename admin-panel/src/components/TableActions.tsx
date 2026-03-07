import React from 'react';

interface TableActionsProps {
  onView?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onMore?: () => void;
  loading?: boolean;
}

export const TableActions: React.FC<TableActionsProps> = ({
  onView,
  onEdit,
  onDelete,
  onMore,
  loading = false,
}) => {
  return (
    <div className="flex items-center gap-1.5">
      {onView && (
        <button
          onClick={onView}
          disabled={loading}
          className="p-2 text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed group relative"
          title="View details"
          aria-label="View details"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-text-primary dark:bg-dark-text-primary text-white dark:text-black text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            View
          </span>
        </button>
      )}

      {onEdit && (
        <button
          onClick={onEdit}
          disabled={loading}
          className="p-2 text-secondary-600 dark:text-secondary-400 hover:bg-secondary-50 dark:hover:bg-secondary-900/30 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed group relative"
          title="Edit"
          aria-label="Edit"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-text-primary dark:bg-dark-text-primary text-white dark:text-black text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Edit
          </span>
        </button>
      )}

      {onDelete && (
        <button
          onClick={onDelete}
          disabled={loading}
          className="p-2 text-error dark:text-red-400 hover:bg-error/10 dark:hover:bg-error/20 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed group relative"
          title="Delete"
          aria-label="Delete"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-error text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Delete
          </span>
        </button>
      )}

      {onMore && (
        <button
          onClick={onMore}
          disabled={loading}
          className="p-2 text-text-secondary dark:text-dark-text-secondary hover:bg-bg-tertiary dark:hover:bg-dark-bg-tertiary rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed group relative"
          title="More actions"
          aria-label="More actions"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
          </svg>
          <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-text-primary dark:bg-dark-text-primary text-white dark:text-black text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            More
          </span>
        </button>
      )}
    </div>
  );
};

export const TableActionsCompact: React.FC<TableActionsProps> = ({
  onView,
  onEdit,
  onDelete,
  onMore,
  loading = false,
}) => {
  return (
    <div className="flex items-center gap-1">
      {onView && (
        <button
          onClick={onView}
          disabled={loading}
          className="px-2 py-1 text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/40 rounded transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          title="View"
        >
          View
        </button>
      )}

      {onEdit && (
        <button
          onClick={onEdit}
          disabled={loading}
          className="px-2 py-1 text-xs font-medium text-secondary-600 dark:text-secondary-400 bg-secondary-50 dark:bg-secondary-900/20 hover:bg-secondary-100 dark:hover:bg-secondary-900/40 rounded transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Edit"
        >
          Edit
        </button>
      )}

      {onDelete && (
        <button
          onClick={onDelete}
          disabled={loading}
          className="px-2 py-1 text-xs font-medium text-error dark:text-red-400 bg-error/10 dark:bg-error/20 hover:bg-error/20 dark:hover:bg-error/30 rounded transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Delete"
        >
          Delete
        </button>
      )}

      {onMore && (
        <button
          onClick={onMore}
          disabled={loading}
          className="px-2 py-1 text-xs font-medium text-text-secondary dark:text-dark-text-secondary bg-bg-tertiary dark:bg-dark-bg-tertiary hover:bg-bg-hover dark:hover:bg-dark-bg-hover rounded transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          title="More"
        >
          ⋯
        </button>
      )}
    </div>
  );
};

// Button group for table header actions
interface TableHeaderActionsProps {
  onAddNew?: () => void;
  onExport?: () => void;
  onImport?: () => void;
  onRefresh?: () => void;
}

export const TableHeaderActions: React.FC<TableHeaderActionsProps> = ({
  onAddNew,
  onExport,
  onImport,
  onRefresh,
}) => {
  return (
    <div className="flex items-center gap-2">
      {onAddNew && (
        <button
          onClick={onAddNew}
          className="inline-flex items-center gap-2 px-3 py-2 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white text-sm font-medium rounded-lg transition-colors duration-200 shadow-sm hover:shadow-md"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add New
        </button>
      )}

      {onRefresh && (
        <button
          onClick={onRefresh}
          className="p-2 text-text-secondary dark:text-dark-text-secondary hover:bg-bg-tertiary dark:hover:bg-dark-bg-tertiary rounded-lg transition-colors duration-200"
          title="Refresh"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      )}

      {onExport && (
        <button
          onClick={onExport}
          className="p-2 text-text-secondary dark:text-dark-text-secondary hover:bg-bg-tertiary dark:hover:bg-dark-bg-tertiary rounded-lg transition-colors duration-200"
          title="Export"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      )}

      {onImport && (
        <button
          onClick={onImport}
          className="p-2 text-text-secondary dark:text-dark-text-secondary hover:bg-bg-tertiary dark:hover:bg-dark-bg-tertiary rounded-lg transition-colors duration-200"
          title="Import"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      )}
    </div>
  );
};
