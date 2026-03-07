import React from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'info' | 'neutral';
  size?: 'sm' | 'md';
}

const variants = {
  primary: 'bg-primary-100 text-primary-700 border border-primary-300 dark:bg-primary-900/40 dark:text-primary-200 dark:border-primary-700',
  secondary: 'bg-secondary-100 text-secondary-700 border border-secondary-300 dark:bg-secondary-900/40 dark:text-secondary-200 dark:border-secondary-700',
  accent: 'bg-accent-100 text-accent-700 border border-accent-300 dark:bg-accent-900/40 dark:text-accent-200 dark:border-accent-700',
  success: 'bg-success-light dark:bg-emerald-900/40 text-success-DEFAULT dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700',
  warning: 'bg-warning-light dark:bg-amber-900/40 text-warning-DEFAULT dark:text-amber-300 border border-amber-300 dark:border-amber-700',
  error: 'bg-error-light dark:bg-red-900/40 text-error dark:text-red-300 border border-red-300 dark:border-red-700',
  info: 'bg-info-light dark:bg-cyan-900/40 text-info-DEFAULT dark:text-cyan-300 border border-cyan-300 dark:border-cyan-700',
  neutral: 'bg-neutral-100 text-neutral-700 border border-neutral-300 dark:bg-neutral-700 dark:text-neutral-200 dark:border-neutral-600',
};

const sizes = {
  sm: 'px-2.5 py-1 text-xs font-semibold',
  md: 'px-3 py-1.5 text-sm font-semibold',
};

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'primary', size = 'sm', className = '', children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={`
          inline-flex items-center gap-1.5 rounded-full
          transition-colors duration-200
          ${variants[variant]}
          ${sizes[size]}
          ${className}
        `}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  type?: 'success' | 'warning' | 'error' | 'info';
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  icon?: React.ReactNode;
}

const alertVariants = {
  success: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-900 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800',
  warning: 'bg-amber-50 dark:bg-amber-900/20 text-amber-900 dark:text-amber-200 border border-amber-200 dark:border-amber-800',
  error: 'bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-200 border border-red-200 dark:border-red-800',
  info: 'bg-cyan-50 dark:bg-cyan-900/20 text-cyan-900 dark:text-cyan-200 border border-cyan-200 dark:border-cyan-800',
};

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    { type = 'info', title, dismissible = false, onDismiss, icon, className = '', children, ...props },
    ref
  ) => {
    const [visible, setVisible] = React.useState(true);

    if (!visible) return null;

    return (
      <div
        ref={ref}
        className={`
          p-4 rounded-lg shadow-elevation-1
          ${alertVariants[type]}
          ${className}
        `}
        {...props}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            {icon && <span className="flex-shrink-0 mt-0.5 text-lg">{icon}</span>}
            <div>
              {title && <h3 className="font-semibold mb-0.5">{title}</h3>}
              <div className="text-sm opacity-90 leading-relaxed">{children}</div>
            </div>
          </div>
          {dismissible && (
            <button
              onClick={() => {
                setVisible(false);
                onDismiss?.();
              }}
              className="flex-shrink-0 text-xl leading-none hover:opacity-70 transition-opacity p-0.5"
              aria-label="Dismiss"
            >
              ×
            </button>
          )}
        </div>
      </div>
    );
  }
);

Alert.displayName = 'Alert';

