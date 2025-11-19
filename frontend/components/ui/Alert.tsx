import React from 'react'

export interface AlertProps {
  variant?: 'default' | 'destructive'
  children: React.ReactNode
  className?: string
}

export const Alert: React.FC<AlertProps> = ({ variant = 'default', children, className = '' }) => {
  const variants = {
    default: 'bg-blue-50 border-blue-200 text-blue-900',
    destructive: 'bg-red-50 border-red-200 text-red-900'
  }
  
  return (
    <div className={`relative w-full rounded-lg border p-4 ${variants[variant]} ${className}`}>
      {children}
    </div>
  )
}

export const AlertDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div className="text-sm">{children}</div>
}
