import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TrendPoint } from "../../types";

export function SeverityTrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        No scans yet — trend will appear here once scans are recorded.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
        <XAxis
          dataKey="date"
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
          contentStyle={{
            background: "var(--chart-surface)",
            border: "1px solid var(--chart-grid)",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: "var(--chart-text-secondary)" }}
        />
        <Line
          type="monotone"
          dataKey="count"
          name="Scans"
          stroke="var(--chart-1)"
          strokeWidth={2}
          dot={{ r: 3, fill: "var(--chart-1)" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
