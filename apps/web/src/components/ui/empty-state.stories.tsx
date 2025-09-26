import React from "react";
import { EmptyState } from "./empty-state";
import { Button } from "./button";

export default { title: "UI/EmptyState" };

export const Basic = () => (
  <EmptyState
    title="No results found"
    description="Try adjusting your filters or create a new item."
    action={<Button size="sm">Create</Button>}
  />
);
