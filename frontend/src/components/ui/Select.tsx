import React from 'react';
import { cn } from '../../utils/cn';

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  success?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  fullWidth?: boolean;
}

const Select: React.FC<SelectProps> = ({
  className,
  label,
  error,
  success,
  helperText,
  options,
  placeholder,
  fullWidth = true,
  ...props
}) => {
  const selectClasses = cn(
    'w-full px-3 py-2 text-sm border border-neutral-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors',
    error && 'border-error-500 focus:ring-error-500 focus:border-error-500',
    success && 'border-success-500 focus:ring-success-500 focus:border-success-500',
    fullWidth && 'w-full',
    className
  );

  return (
    <div className={cn('space-y-1', fullWidth && 'w-full')}>
      {label && (
        <label className="block text-sm font-medium text-neutral-700">
          {label}
        </label>
      )}
      <select className={selectClasses} {...props}>
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
      {(error || success || helperText) && (
        <p className={cn(
          'text-sm',
          error && 'text-error-600',
          success && 'text-success-600',
          !error && !success && 'text-neutral-500'
        )}>
          {error || success || helperText}
        </p>
      )}
    </div>
  );
};

export default Select;
