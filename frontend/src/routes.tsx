import { Routes, Route } from "react-router-dom";
import { BasicLayout } from "./components/layout/BasicLayout";
import { HomePage } from "./pages/HomePage";
import { MarketsPage } from "./pages/MarketsPage";
import { AnalyzePage } from "./pages/AnalyzePage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<BasicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/markets" element={<MarketsPage />} />
        <Route path="/analyze" element={<AnalyzePage />} />
      </Route>
    </Routes>
  );
}
