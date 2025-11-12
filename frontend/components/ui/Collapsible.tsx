'use client'

import React, { useState } from 'react'

export interface CollapsibleProps {
  children: React.ReactNode
  className?: string
}

export const Collapsible: React.FC<CollapsibleProps> = ({ children, className = '' }) => {
  const [open, setOpen] = useState(false)
  
  return (
    <div className={className} data-open={open}>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<any>, { open, setOpen })
        }
        return child
      })}
    </div>
  )
}

export const CollapsibleTrigger: React.FC<{ children: React.ReactNode; open?: boolean; setOpen?: (open: boolean) => void }> = ({ children, open, setOpen }) => {
  return (
    <div onClick={() => setOpen?.(!open)} className="cursor-pointer">
      {children}
    </div>
  )
}

export const CollapsibleContent: React.FC<{ children: React.ReactNode; open?: boolean }> = ({ children, open }) => {
  if (!open) return null
  return <div>{children}</div>
}
