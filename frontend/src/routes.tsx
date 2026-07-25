import { Routes, Route } from "react-router-dom";
import { BasicLayout } from "./components/layout/BasicLayout";
import { HomePage } from "./pages/HomePage";
import { MarketsPage } from "./pages/MarketsPage";
import { AnalyzePage } from "./pages/AnalyzePage";
import { BacktestPage } from "./pages/BacktestPage";
import { RunsPage } from "./pages/RunsPage";
import { RunDetailPage } from "./pages/RunDetailPage";
import { WatchlistPage } from "./pages/WatchlistPage";
import { TradingPage } from "./pages/TradingPage";
import { StrategyEditorPage } from "./pages/StrategyEditorPage";
import { DebatePage } from "./pages/DebatePage";

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
        <Route path="/trading" element={<TradingPage />} />
        <Route path="/strategy-editor" element={<StrategyEditorPage />} />
        <Route path="/debate" element={<DebatePage />} />
      </Route>
    </Routes>
  );
}
