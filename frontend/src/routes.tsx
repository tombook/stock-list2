import { Routes, Route } from "react-router-dom";
import { BasicLayout } from "./components/layout/BasicLayout";
import { HomePage } from "./pages/HomePage";
import { MarketsPage } from "./pages/MarketsPage";
import { AnalyzePage } from "./pages/AnalyzePage";
import { BacktestPage } from "./pages/BacktestPage";
import { RunsPage } from "./pages/RunsPage";
import { RunDetailPage } from "./pages/RunDetailPage";
import { WatchlistPage } from "./pages/WatchlistPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<BasicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/markets" element={<MarketsPage />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/backtest" element={<BacktestPage />} />
        <Route path="/runs" element={<RunsPage />} />
        <Route path="/runs/:id" element={<RunDetailPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
      </Route>
    </Routes>
  );
}
