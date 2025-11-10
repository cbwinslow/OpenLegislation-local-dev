import React from 'react'

export interface ProgressProps {
  value?: number
  className?: string
}

export const Progress: React.FC<ProgressProps> = ({ value = 0, className = '' }) => {
  return (
    <div className={`relative h-4 w-full overflow-hidden rounded-full bg-gray-100 ${className}`}>
      <div
        className="h-full bg-blue-600 transition-all duration-300 ease-in-out"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}
