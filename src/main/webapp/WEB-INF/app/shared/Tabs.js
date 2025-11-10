import React, { createContext, useContext, useState } from 'react';

const TabsContext = createContext();

export const Tabs = ({ value, onValueChange, children, className = '', ...props }) => {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={className} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

export const TabsList = ({ children, className = '', ...props }) => {
  return (
    <div className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500 ${className}`} {...props}>
      {children}
    </div>
  );
};

export const TabsTrigger = ({ value, children, className = '', ...props }) => {
  const { value: selectedValue, onValueChange } = useContext(TabsContext);
  const isSelected = selectedValue === value;

  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        isSelected
          ? 'bg-white text-gray-950 shadow-sm'
          : 'text-gray-500 hover:text-gray-900'
      } ${className}`}
      onClick={() => onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({ value, children, className = '', ...props }) => {
  const { value: selectedValue } = useContext(TabsContext);

  if (selectedValue !== value) return null;

  return (
    <div className={`mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2 ${className}`} {...props}>
      {children}
    </div>
  );
};
