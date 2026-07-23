import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";
import { AppRoutes } from "./routes";
import { useAppStore } from "./stores/appStore";
import { useEffect } from "react";

export function App() {
  const theme = useAppStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <BrowserRouter>
      <AppRoutes />
      <Toaster position="bottom-right" theme={theme} />
    </BrowserRouter>
  );
}
