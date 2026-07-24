import { NavLink, Outlet } from "react-router-dom";
import { Activity, BarChart3, Bookmark, FlaskConical, History, MessageSquare, Moon, Sun } from "lucide-react";;
import { useAppStore } from "../../stores/appStore";
import { cn } from "../../lib/cn";

const nav = [
  { to: "/", label: "Home", icon: Activity },
  { to: "/markets", label: "Markets", icon: BarChart3 },
  { to: "/analyze", label: "Analyze", icon: MessageSquare },
  { to: "/backtest", label: "Backtest", icon: FlaskConical },
  { to: "/runs", label: "Runs", icon: History },
  { to: "/watchlist", label: "Watchlist", icon: Bookmark },
];

export function BasicLayout() {
  const { theme, toggleTheme, sidebarCollapsed } = useAppStore();

  return (
    <div className="flex h-screen">
      <aside
        className={cn(
          "flex flex-col border-r border-slate-200 bg-white transition-all dark:border-slate-800 dark:bg-slate-900",
          sidebarCollapsed ? "w-16" : "w-56",
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b border-slate-200 px-4 dark:border-slate-800">
          <span className="text-lg font-bold text-brand">stock-list2</span>
        </div>
        <nav className="flex-1 space-y-1 p-2">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm",
                  isActive
                    ? "bg-brand/10 text-brand"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
                )
              }
            >
              <Icon size={18} />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-end gap-2 border-b border-slate-200 px-4 dark:border-slate-800">
          <button
            onClick={toggleTheme}
            className="rounded-md p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
