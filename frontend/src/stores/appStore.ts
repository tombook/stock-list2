import { create } from "zustand";

type Theme = "light" | "dark";
const KEY = "sl2-theme";

function initialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const saved = window.localStorage.getItem(KEY);
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export interface AppState {
  theme: Theme;
  sidebarCollapsed: boolean;
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  theme: initialTheme(),
  sidebarCollapsed: false,
  toggleTheme: () => {
    const next: Theme = get().theme === "dark" ? "light" : "dark";
    if (typeof window !== "undefined") window.localStorage.setItem(KEY, next);
    if (typeof document !== "undefined") document.documentElement.classList.toggle("dark", next === "dark");
    set({ theme: next });
  },
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
