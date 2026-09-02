import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./routes/DashboardPage";
import { HistoryPage } from "./routes/HistoryPage";
import { ResultPage } from "./routes/ResultPage";
import { ScanPage } from "./routes/ScanPage";

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<ScanPage />} />
        <Route path="/result/:scanUuid" element={<ResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
        {/* Detail view is the same result layout, just reached from history */}
        <Route path="/history/:scanUuid" element={<ResultPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
