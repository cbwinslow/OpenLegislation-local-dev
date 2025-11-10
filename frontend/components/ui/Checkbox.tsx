'use client'

import React from 'react'

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onCheckedChange?: (checked: boolean) => void
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = '', onCheckedChange, onChange, checked, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(e)
      onCheckedChange?.(e.target.checked)
    }
    
    return (
      <input
        ref={ref}
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        className={`h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${className}`}
        {...props}
      />
    )
  }
)

Checkbox.displayName = 'Checkbox'
