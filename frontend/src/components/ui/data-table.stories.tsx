import React from "react";
import { DataTable } from "./data-table";

type Row = { name: string; pos: string; points: number };
const rows: Row[] = [
  { name: "Alice Adams", pos: "PG", points: 25.4 },
  { name: "Bob Brown", pos: "SG", points: 18.1 },
  { name: "Carla Cruz", pos: "SF", points: 22.7 },
  { name: "Derek Doe", pos: "PF", points: 15.3 },
  { name: "Eve Evans", pos: "C", points: 28.9 },
  { name: "Fred Flynn", pos: "PG", points: 11.2 },
  { name: "Gina Green", pos: "SG", points: 19.8 },
  { name: "Hank Hill", pos: "SF", points: 9.1 },
  { name: "Ivy Irwin", pos: "PF", points: 13.6 },
  { name: "Jackie Jones", pos: "C", points: 26.4 },
  { name: "Kurt King", pos: "PG", points: 7.8 },
  { name: "Lily Lane", pos: "SG", points: 16.0 },
  { name: "Mona Mitchell", pos: "SF", points: 21.3 },
  { name: "Nate North", pos: "PF", points: 14.2 },
  { name: "Omar Ortiz", pos: "C", points: 27.1 },
];

export default { title: "UI/DataTable" };

export const Basic = () => (
  <DataTable<Row>
    columns={[
      { key: "name", header: "Name", sortable: true },
      { key: "pos", header: "Pos", sortable: true },
      { key: "points", header: "PTS", sortable: true },
    ]}
    data={rows}
    initialSort={{ key: "points", dir: "desc" }}
    pageSize={5}
    storageKey="players"
    shareKey="v"
  />
);
