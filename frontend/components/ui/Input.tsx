import * as React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: string;
  error?: string;
  fullWidth?: boolean;
}

export function Input({
  className = '',
  icon,
  error,
  fullWidth = true,
  ...props
}: InputProps) {
  return (
    <div className={`relative ${fullWidth ? 'w-full' : 'inline-block'}`}>
      {icon && (
        <span className="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-outline">
          {icon}
        </span>
      )}
      <input
        className={`
          flex h-14 w-full rounded-xl border-none bg-surface-container px-4 text-sm text-on-surface 
          placeholder:text-on-surface-variant outline-none transition-all
          focus:ring-2 focus:ring-primary/20 
          ${icon ? 'pl-12' : ''}
          ${error ? 'ring-2 ring-error/50 focus:ring-error text-error' : ''}
          ${className}
        `}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-error">{error}</p>}
    </div>
  );
}
