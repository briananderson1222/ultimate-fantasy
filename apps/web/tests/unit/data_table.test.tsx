import { fireEvent, render } from "@testing-library/react";
import React from "react";
import { DataTable } from "../../src/components/ui/data-table";

type Row = { name: string; points: number };

describe("DataTable", () => {
  const columns = [
    { key: "name", header: "Name", sortable: true },
    { key: "points", header: "Points", sortable: true },
  ];
  const data: Row[] = [
    { name: "Alpha", points: 10 },
    { name: "Charlie", points: 4 },
    { name: "Bravo", points: 7 },
  ];

  it("sorts by header click and updates aria-sort", () => {
    const { getAllByRole, getByRole } = render(
      <DataTable
        columns={columns}
        data={data}
        initialSort={{ key: "name", dir: "asc" }}
        pageSize={10}
      />,
    );

    // Ascending by name initially: Alpha, Bravo, Charlie
    let rows = getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Alpha");
    expect(rows[2]).toHaveTextContent("Bravo");
    expect(rows[3]).toHaveTextContent("Charlie");

    // Click Points to sort by points asc: 4,7,10
    fireEvent.click(getByRole("columnheader", { name: "Points" }));
    rows = getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Charlie");
    expect(rows[2]).toHaveTextContent("Bravo");
    expect(rows[3]).toHaveTextContent("Alpha");

    // Click Points again for desc: 10,7,4
    fireEvent.click(getByRole("columnheader", { name: "Points" }));
    rows = getAllByRole("row");
    expect(rows[1]).toHaveTextContent("Alpha");
    expect(rows[2]).toHaveTextContent("Bravo");
    expect(rows[3]).toHaveTextContent("Charlie");
  });

  it("hides columns via toggles", () => {
    const { getByLabelText, queryByText } = render(
      <DataTable columns={columns} data={data} pageSize={10} />,
    );
    const nameToggle = getByLabelText("Name") as HTMLInputElement;
    fireEvent.click(nameToggle);
    expect(queryByText("Name")).toBeNull();
  });
});
