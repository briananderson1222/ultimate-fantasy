import React from 'react';
import { Button } from './button';
import { Trophy } from 'lucide-react';

export default { title: 'UI/Button' };

export const Primary = () => <Button>Primary</Button>;
export const Secondary = () => <Button variant="secondary">Secondary</Button>;
export const Ghost = () => <Button variant="ghost">Ghost</Button>;
export const Sizes = () => (
  <div className="flex items-center gap-3">
    <Button size="sm">Small</Button>
    <Button size="md">Medium</Button>
    <Button size="lg">Large</Button>
  </div>
);
export const WithIcon = () => (
  <Button leftIcon={<Trophy aria-hidden className="h-4 w-4" />}>With Icon</Button>
);
export const Loading = () => <Button loading>Loading…</Button>;

