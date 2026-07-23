import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth } from "../api/health";
import type { Health } from "../types/market";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

export function HomePage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((h) => !cancelled && setHealth(h))
      .catch((e: unknown) => !cancelled && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">stock-list2</h1>
      <p className="text-slate-600 dark:text-slate-400">
        Async, type-safe trading-research core. Type a ticker to pull live data.
      </p>

      <Card>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-500 dark:text-slate-400">Backend health</span>
          <span
            className={
              "rounded px-2 py-0.5 text-xs font-semibold " +
              (health?.status === "healthy"
                ? "bg-emerald-100 text-emerald-700"
                : health?.status === "degraded"
                  ? "bg-amber-100 text-amber-700"
                  : "bg-slate-200 text-slate-600")
            }
          >
            {error ? "unreachable" : (health?.status ?? "checking…")}
          </span>
        </div>
        {health && (
          <ul className="mt-3 space-y-1 text-sm">
            {Object.entries(health.dependencies).map(([name, dep]) => (
              <li key={name} className="flex justify-between">
                <span>{name}</span>
                <span className={dep.status === "ok" ? "text-emerald-600" : "text-amber-600"}>{dep.status}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Link to="/markets">
        <Button>Open markets →</Button>
      </Link>
    </div>
  );
}
