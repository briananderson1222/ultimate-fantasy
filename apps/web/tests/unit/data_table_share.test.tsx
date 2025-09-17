import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { DataTable } from "../../src/components/ui/data-table";

type Row = { name: string; points: number };

describe("DataTable share view", () => {
  const columns = [
    { key: "name", header: "Name", sortable: true },
    { key: "points", header: "Points", sortable: true },
  ];
  const data: Row[] = [{ name: "Alpha", points: 10 }];

  beforeEach(() => {
    localStorage.clear();
  });

  it("copies a shareable link with the query param", async () => {
    // Mock clipboard
    // @ts-ignore
    global.navigator.clipboard = { writeText: vi.fn().mockResolvedValue(undefined) };

    render(
      <DataTable
        columns={columns}
        data={data}
        pageSize={10}
        storageKey="share-test"
        shareKey="dt"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /share link/i }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledTimes(1);
    const url = (navigator.clipboard.writeText as any).mock.calls[0][0] as string;
    expect(url).toContain("dt=");
  });
});
