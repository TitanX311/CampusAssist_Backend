import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  bordered?: boolean;
  hoverable?: boolean;
  elevation?: 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ bordered = true, hoverable = false, elevation = 'sm', className = '', children, ...props }, ref) => {
    const elevationClass = {
      sm: 'shadow-elevation-1',
      md: 'shadow-elevation-2',
      lg: 'shadow-elevation-3',
    }[elevation];

    return (
      <div
        ref={ref}
        className={`
          bg-bg-primary dark:bg-dark-bg-primary rounded-lg
          ${bordered ? 'border border-border-primary dark:border-dark-border-primary' : ''}
          ${elevationClass}
          ${hoverable ? 'hover:shadow-elevation-2 dark:hover:shadow-elevation-3 cursor-pointer' : ''}
          transition-all duration-200
          overflow-hidden
          ${className}
        `}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', children, ...props }, ref) => (
    <div
      ref={ref}
      className={`
        px-6 py-5 border-b border-border-primary dark:border-dark-border-primary
        bg-bg-secondary dark:bg-dark-bg-secondary
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  )
);

CardHeader.displayName = 'CardHeader';

export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', children, ...props }, ref) => (
    <div
      ref={ref}
      className={`
        p-6
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  )
);

CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', children, ...props }, ref) => (
    <div
      ref={ref}
      className={`
        px-6 py-4 border-t border-border-primary dark:border-dark-border-primary
        bg-bg-secondary dark:bg-dark-bg-secondary
        flex items-center justify-between gap-3
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  )
);
CardFooter.displayName = 'CardFooter';

