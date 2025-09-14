import React, { useState } from "react";
import { Modal } from "./modal";
import { Button } from "./button";

export default { title: "UI/Modal" };

export const Basic = () => {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal open={open} onClose={() => setOpen(false)} title="Example Modal">
        <p className="text-sm text-gray-700">Hello from inside the modal.</p>
      </Modal>
    </div>
  );
};
