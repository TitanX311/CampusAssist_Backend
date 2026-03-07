import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
}

const variants = {
  primary: `
    bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white
    dark:bg-primary-600 dark:hover:bg-primary-500 dark:active:bg-primary-700
    shadow-sm border border-primary-600 dark:border-primary-700
    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-900
  `,
  secondary: `
    bg-secondary-100 hover:bg-secondary-200 active:bg-secondary-300 text-secondary-700
    dark:bg-secondary-900/30 dark:hover:bg-secondary-900/50 dark:active:bg-secondary-900/70 dark:text-secondary-100
    border border-secondary-200 dark:border-secondary-800
    focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-900
  `,
  danger: `
    bg-error hover:bg-red-700 active:bg-red-800 text-white
    dark:bg-error dark:hover:bg-red-700 dark:active:bg-red-800
    shadow-sm border border-error
    focus:outline-none focus:ring-2 focus:ring-error focus:ring-offset-2 dark:focus:ring-offset-neutral-900
  `,
  outline: `
    bg-bg-primary hover:bg-bg-secondary active:bg-bg-tertiary text-text-primary
    dark:bg-dark-bg-primary dark:hover:bg-dark-bg-secondary dark:active:bg-dark-bg-tertiary dark:text-dark-text-primary
    border border-border-primary dark:border-dark-border-primary
    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-900
  `,
  ghost: `
    bg-transparent hover:bg-bg-secondary active:bg-bg-tertiary text-text-primary
    dark:hover:bg-dark-bg-secondary dark:active:bg-dark-bg-tertiary dark:text-dark-text-primary
    focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-neutral-900
  `,
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm font-medium rounded-md gap-2',
  md: 'px-4 py-2 text-sm font-medium rounded-md gap-2',
  lg: 'px-5 py-2.5 text-base font-semibold rounded-lg gap-2',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      icon,
      disabled = false,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`
          inline-flex items-center justify-center
          transition-all duration-200 ease-in-out
          ${variants[variant]}
          ${sizes[size]}
          ${fullWidth ? 'w-full' : ''}
          disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none
          ${className}
        `}
        {...props}
      >
        {loading ? (
          <>
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {children}
          </>
        ) : (
          <>
            {icon && <span className="flex-shrink-0">{icon}</span>}
            {children}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';