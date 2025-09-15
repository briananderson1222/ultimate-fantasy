import React from "react";
import { Card, CardHeader, CardTitle } from "./card";
import { Button } from "./button";

export default { title: "UI/Card" };

export const Basic = () => (
  <Card>
    <CardHeader>
      <CardTitle>Card Title</CardTitle>
      <Button size="sm">Action</Button>
    </CardHeader>
    <p className="text-sm text-gray-700">This is a simple card body.</p>
  </Card>
);
