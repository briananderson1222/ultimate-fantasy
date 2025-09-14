import { fireEvent, render } from "@testing-library/react";
import React from "react";
import { Tabs } from "../../src/components/ui/tabs";

describe("Tabs a11y + keyboard", () => {
  it("uses roving tabindex and arrow keys to change tabs", () => {
    const tabs = [
      { value: "overview", label: "Overview" },
      { value: "scoreboard", label: "Scoreboard" },
      { value: "managers", label: "Managers" },
    ];
    let value = "overview";
    const onChange = (v: string) => {
      value = v;
      rerender(<Tabs tabs={tabs} value={value} onChange={onChange} />);
    };

    const { getByRole, getAllByRole, rerender } = render(
      <Tabs tabs={tabs} value={value} onChange={onChange} />,
    );

    const tablist = getByRole("tablist");
    const buttons = getAllByRole("tab");
    expect(buttons[0]).toHaveAttribute("tabindex", "0");
    expect(buttons[1]).toHaveAttribute("tabindex", "-1");

    fireEvent.keyDown(tablist, { key: "ArrowRight" });
    const buttons2 = getAllByRole("tab");
    expect(buttons2[1]).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(tablist, { key: "ArrowLeft" });
    const buttons3 = getAllByRole("tab");
    expect(buttons3[0]).toHaveAttribute("aria-selected", "true");
  });
});
