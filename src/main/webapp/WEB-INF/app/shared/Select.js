import React from 'react';

export const Select = ({ className = '', children, ...props }) => {
  const baseClasses = 'flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50';

  return (
    <select className={`${baseClasses} ${className}`} {...props}>
      {children}
    </select>
  );
};
