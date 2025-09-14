import React from "react";
import { Skeleton } from "./skeleton";

export default { title: "UI/Skeleton" };

export const Lines = () => (
  <div className="space-y-2">
    <Skeleton className="h-4 w-[240px]" />
    <Skeleton className="h-4 w-[280px]" />
    <Skeleton className="h-4 w-[200px]" />
  </div>
);
