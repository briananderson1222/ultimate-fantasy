import { render } from "@testing-library/react";
import React from "react";
import RootLayout from "../../src/app/layout";

describe("Skip link", () => {
  it("renders a skip to content link", () => {
    const { getByRole } = render(
      (
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      ) as any,
    );
    const link = getByRole("link", { name: /skip to content/i });
    expect(link).toHaveAttribute("href", "#main");
  });
});
