import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { DataTable } from "../../src/components/ui/data-table";

type Row = { name: string; points: number };

describe("DataTable saved views", () => {
  const columns = [
    { key: "name", header: "Name", sortable: true },
    { key: "points", header: "Points", sortable: true },
  ];
  const data: Row[] = [
    { name: "Alpha", points: 10 },
    { name: "Charlie", points: 4 },
    { name: "Bravo", points: 7 },
  ];

  beforeEach(() => {
    localStorage.clear();
  });

  it("saves and applies a view via localStorage", () => {
    // Mock prompt
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("HideName");

    render(<DataTable columns={columns} data={data} storageKey="test-table" pageSize={10} />);

    // Hide the Name column via toggle
    const nameToggle = screen.getByLabelText("Name") as HTMLInputElement;
    fireEvent.click(nameToggle);
    expect(screen.queryByRole("columnheader", { name: "Name" })).toBeNull();

    // Save the current view
    fireEvent.click(screen.getByRole("button", { name: /save view/i }));

    // Change state back (show Name)
    fireEvent.click(nameToggle);
    expect(screen.getByRole("columnheader", { name: "Name" })).toBeInTheDocument();

    // Apply saved view by selecting it
    const select = screen.getByLabelText("Saved views") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "HideName" } });
    expect(screen.queryByRole("columnheader", { name: "Name" })).toBeNull();

    promptSpy.mockRestore();
  });
});
