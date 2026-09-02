import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SUPPORTED_CROPS } from "../../types";
import type { BreakdownItem } from "../../types";

// Fixed hue-per-crop assignment (never reassigned based on which crops are
// present in the current data) — matches the validated categorical order in
// src/styles/index.css.
const CROP_COLOR_VARS: Record<string, string> = {
  Apple: "var(--chart-1)",
  Grape: "var(--chart-2)",
  Corn: "var(--chart-3)",
  Tomato: "var(--chart-4)",
  Strawberry: "var(--chart-5)",
  Peach: "var(--chart-6)",
};

export function CropDistributionChart({ data }: { data: BreakdownItem[] }) {
  // Always render all 6 supported crops (0-count bars included) so the chart
  // reads consistently across time ranges instead of reshuffling categories.
  const chartData = SUPPORTED_CROPS.map((crop) => ({
    label: crop,
    count: data.find((item) => item.label === crop)?.count ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="label"
          stroke="var(--chart-axis)"
          tick={{ fill: "var(--chart-text-secondary)", fontSize: 12 }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          stroke="var(--chart-axis)"
          tick={{ fill: "var(--chart-text-secondary)", fontSize: 12 }}
          tickLine={false}
          width={32}
        />
        <Tooltip
          cursor={{ fill: "var(--chart-grid)", opacity: 0.4 }}
          contentStyle={{
            background: "var(--chart-surface)",
            border: "1px solid var(--chart-grid)",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: "var(--chart-text-secondary)" }}
        />
        <Bar dataKey="count" name="Scans" radius={[4, 4, 0, 0]}>
          {chartData.map((entry) => (
            <Cell key={entry.label} fill={CROP_COLOR_VARS[entry.label]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
