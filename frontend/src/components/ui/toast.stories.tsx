import React from 'react';
import { Button } from './button';
import { useToast } from './toast';

export default { title: 'UI/Toast' };

export const Basic = () => {
  const { show } = useToast();
  return (
    <Button
      onClick={() => show({ title: 'Saved', description: 'Your changes have been saved.' })}
    >
      Show Toast
    </Button>
  );
};

