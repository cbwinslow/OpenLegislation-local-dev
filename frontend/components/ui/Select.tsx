'use client'

import React, { createContext, useContext, useState } from 'react'

interface SelectContextType {
  value: string
  onValueChange: (value: string) => void
}

const SelectContext = createContext<SelectContextType | undefined>(undefined)

export interface SelectProps {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}

export const Select: React.FC<SelectProps> = ({ defaultValue, value, onValueChange, children }) => {
  const [internalValue, setInternalValue] = useState(defaultValue || '')
  const currentValue = value !== undefined ? value : internalValue
  
  const handleValueChange = (newValue: string) => {
    if (value === undefined) {
      setInternalValue(newValue)
    }
    onValueChange?.(newValue)
  }
  
  return (
    <SelectContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
      {children}
    </SelectContext.Provider>
  )
}

export interface SelectTriggerProps {
  children?: React.ReactNode
  className?: string
}

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ children, className = '' }) => {
  return (
    <div className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}>
      {children}
    </div>
  )
}

export const SelectValue: React.FC = () => {
  const context = useContext(SelectContext)
  return <span>{context?.value || 'Select...'}</span>
}

export interface SelectContentProps {
  children: React.ReactNode
}

export const SelectContent: React.FC<SelectContentProps> = ({ children }) => {
  return (
    <div className="relative z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white text-gray-950 shadow-md">
      <div className="p-1">{children}</div>
    </div>
  )
}

export interface SelectItemProps {
  value: string
  children: React.ReactNode
}

export const SelectItem: React.FC<SelectItemProps> = ({ value, children }) => {
  const context = useContext(SelectContext)
  
  return (
    <div
      className="relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100"
      onClick={() => context?.onValueChange(value)}
    >
      {children}
    </div>
  )
}
