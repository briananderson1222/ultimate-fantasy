import React from 'react';
import '../src/app/globals.css';
import Providers from '../src/app/providers';

export const Provider = ({ children }: { children: React.ReactNode }) => {
  return <Providers>{children}</Providers>;
};

