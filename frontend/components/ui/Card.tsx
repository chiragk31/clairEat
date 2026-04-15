import * as React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'elevated' | 'filled' | 'outlined' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({
  className = '',
  variant = 'elevated',
  padding = 'md',
  children,
  ...props
}: CardProps) {
  const baseStyles = 'rounded-2xl transition-all duration-300';
  
  const variants = {
    elevated: 'bg-surface shadow-diffusion hover:shadow-diffusion-md',
    filled: 'bg-surface-container hover:bg-surface-container-high',
    outlined: 'border border-outline-variant bg-transparent',
    glass: 'glass-panel border border-white/20 shadow-sm',
  };

  const paddings = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`${baseStyles} ${variants[variant]} ${paddings[padding]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
