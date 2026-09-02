import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { HistoryTable } from "./HistoryTable";

describe("HistoryTable", () => {
  it("shows an empty state when there are no scans", () => {
    render(
      <MemoryRouter>
        <HistoryTable items={[]} />
      </MemoryRouter>,
    );
    expect(screen.getByText(/no scans match these filters/i)).toBeInTheDocument();
  });

  it("renders a row for each scan", () => {
    render(
      <MemoryRouter>
        <HistoryTable
          items={[
            {
              scan_uuid: "abc-123",
              crop_name: "Tomato",
              disease_display_name: "Late blight",
              confidence: 0.92,
              infected_area_pct: 34.5,
              severity: "Severe",
              overlay_image_url: "/static/uploads/abc-123/overlay.jpg",
              prediction_warning: null,
              created_at: "2026-08-03T10:00:00Z",
            },
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getAllByText(/late blight/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Severe").length).toBeGreaterThan(0);
  });

  it("shows a reliability warning indicator when a scan is flagged", () => {
    render(
      <MemoryRouter>
        <HistoryTable
          items={[
            {
              scan_uuid: "def-456",
              crop_name: "Tomato",
              disease_display_name: "Late blight",
              confidence: 0.92,
              infected_area_pct: 34.5,
              severity: "Severe",
              overlay_image_url: "/static/uploads/def-456/overlay.jpg",
              prediction_warning: "No clear leaf detected — leaf-colored region covers only 0% of the frame.",
              created_at: "2026-08-03T10:00:00Z",
            },
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getAllByLabelText(/reliability warning/i).length).toBeGreaterThan(0);
  });
});
