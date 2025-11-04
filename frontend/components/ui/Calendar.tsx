import React from 'react'

export interface CalendarProps {
  mode?: 'single' | 'range'
  selected?: Date
  onSelect?: (date: Date | undefined) => void
  className?: string
}

export const Calendar: React.FC<CalendarProps> = ({ className = '' }) => {
  return (
    <div className={`p-3 ${className}`}>
      <div className="text-sm text-gray-600">Calendar component - placeholder</div>
    </div>
  )
}
