import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SeverityBadge } from "./SeverityBadge";

describe("SeverityBadge", () => {
  it("renders the severity label as visible text for every level", () => {
    for (const severity of ["Healthy", "Mild", "Moderate", "Severe", "Critical"] as const) {
      const { unmount } = render(<SeverityBadge severity={severity} />);
      expect(screen.getByText(severity)).toBeInTheDocument();
      unmount();
    }
  });
});
