import React from "react";
import { Tabs } from "./tabs";

export default { title: "UI/Tabs" };

export const Basic = () => {
  const [value, setValue] = React.useState("a");
  return (
    <div>
      <Tabs
        tabs={[
          { value: "a", label: "Overview" },
          { value: "b", label: "Scoreboard" },
          { value: "c", label: "Managers" },
        ]}
        value={value}
        onChange={setValue}
      />
      <div className="text-sm text-gray-700">Selected tab: {value}</div>
    </div>
  );
};
