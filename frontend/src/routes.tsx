import { Routes, Route } from "react-router-dom";
import { BasicLayout } from "./components/layout/BasicLayout";
import { HomePage } from "./pages/HomePage";
import { MarketsPage } from "./pages/MarketsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<BasicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/markets" element={<MarketsPage />} />
      </Route>
    </Routes>
  );
}
