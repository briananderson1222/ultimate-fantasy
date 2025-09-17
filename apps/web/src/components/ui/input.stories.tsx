import React, { useState } from "react";
import { Input } from "./input";

export default { title: "UI/Input" };

export const Basic = () => <Input label="Email" placeholder="you@example.com" type="email" />;

export const WithError = () => (
  <Input label="Username" placeholder="username" error="Username is taken" />
);

export const Controlled = () => {
  const [val, setVal] = useState("");
  return (
    <div className="space-y-2">
      <Input label="Controlled" value={val} onChange={(e) => setVal(e.currentTarget.value)} />
      <div className="text-sm text-gray-600">Value: {val || "(empty)"}</div>
    </div>
  );
};
