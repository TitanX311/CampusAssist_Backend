import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, icon, className = '', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-2.5">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-dark-text-tertiary flex-shrink-0">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            className={`
              w-full px-3.5 py-2.5 rounded-md text-sm
              border border-border-primary dark:border-dark-border-primary
              bg-bg-primary dark:bg-dark-bg-secondary
              text-text-primary dark:text-dark-text-primary
              placeholder:text-text-tertiary dark:placeholder:text-dark-text-tertiary
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
              focus:border-transparent dark:focus:ring-offset-neutral-900
              dark:focus:border-transparent
              disabled:bg-bg-secondary dark:disabled:bg-dark-bg-tertiary
              disabled:text-text-tertiary dark:disabled:text-dark-text-tertiary
              disabled:cursor-not-allowed
              disabled:opacity-60
              ${icon ? 'pl-10' : ''}
              ${error ? '!border-error !ring-1 !ring-error/20 dark:!border-error dark:!ring-error/20' : ''}
              ${className}
            `}
            {...props}
          />
        </div>
        {error && (
          <div className="mt-2 text-sm font-medium text-error dark:text-error flex items-center gap-1">
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18.101 12.93l-.門-7.437A1.002 1.002 0 0017 4H3a1 1 0 0 0-.999 1.493l.082 7.437A2 2 0 004.07 15h11.86a2 2 0 001.948-1.57zM9 13a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}
        {helperText && !error && (
          <div className="mt-2 text-xs text-text-tertiary dark:text-dark-text-tertiary">
            {helperText}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  InputProps & React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ label, error, helperText, className = '', ...props }, ref) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-semibold text-text-primary dark:text-dark-text-primary mb-2.5">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        className={`
          w-full px-3.5 py-2.5 rounded-md text-sm
          border border-border-primary dark:border-dark-border-primary
          bg-bg-primary dark:bg-dark-bg-secondary
          text-text-primary dark:text-dark-text-primary
          placeholder:text-text-tertiary dark:placeholder:text-dark-text-tertiary
          transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
          focus:border-transparent dark:focus:ring-offset-neutral-900
          dark:focus:border-transparent
          disabled:bg-bg-secondary dark:disabled:bg-dark-bg-tertiary
          disabled:text-text-tertiary dark:disabled:text-dark-text-tertiary
          disabled:cursor-not-allowed
          disabled:opacity-60
          resize-none
          ${error ? '!border-error !ring-1 !ring-error/20 dark:!border-error dark:!ring-error/20' : ''}
          ${className}
        `}
        {...props}
      />
      {error && (
        <div className="mt-2 text-sm font-medium text-error dark:text-error">
          {error}
        </div>
      )}
      {helperText && !error && (
        <div className="mt-2 text-xs text-text-tertiary dark:text-dark-text-tertiary">
          {helperText}
        </div>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';