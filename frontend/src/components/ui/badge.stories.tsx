import React from 'react';
import { Badge } from './badge';

export default { title: 'UI/Badge' };

export const Variants = () => (
  <div className="flex items-center gap-2">
    <Badge>default</Badge>
    <Badge variant="secondary">secondary</Badge>
    <Badge variant="success">success</Badge>
    <Badge variant="warning">warning</Badge>
    <Badge variant="destructive">destructive</Badge>
  </div>
);

