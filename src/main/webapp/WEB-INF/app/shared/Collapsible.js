import React, { createContext, useContext, useState } from 'react';

const CollapsibleContext = createContext();

export const Collapsible = ({ open, onOpenChange, children, ...props }) => {
  const [isOpen, setIsOpen] = useState(open || false);

  const toggle = () => {
    setIsOpen(!isOpen);
    onOpenChange?.(!isOpen);
  };

  return (
    <CollapsibleContext.Provider value={{ isOpen, toggle }}>
      <div {...props}>
        {children}
      </div>
    </CollapsibleContext.Provider>
  );
};

export const CollapsibleTrigger = ({ children, className = '', ...props }) => {
  const { toggle } = useContext(CollapsibleContext);

  return (
    <button
      type="button"
      className={`flex items-center justify-between w-full p-2 text-left hover:bg-gray-50 ${className}`}
      onClick={toggle}
      {...props}
    >
      {children}
    </button>
  );
};

export const CollapsibleContent = ({ children, className = '', ...props }) => {
  const { isOpen } = useContext(CollapsibleContext);

  if (!isOpen) return null;

  return (
    <div className={`px-2 py-1 ${className}`} {...props}>
      {children}
    </div>
  );
};