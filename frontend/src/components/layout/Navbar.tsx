import { NavLink } from "react-router-dom";
import { useTheme } from "./ThemeProvider";

const LINKS = [
  { to: "/", label: "Scan" },
  { to: "/history", label: "History" },
  { to: "/dashboard", label: "Dashboard" },
];

export function Navbar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="border-b border-surface-border bg-surface-raised">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-brand-light">AgriVision</span>
          <span className="hidden text-xs text-slate-400 sm:inline">Leaf Disease Detection</span>
        </div>

        <nav className="flex items-center gap-1 sm:gap-2">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand/20 text-brand-light"
                    : "text-slate-300 hover:bg-surface-border hover:text-white"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={toggleTheme}
            className="ml-2 rounded-md border border-surface-border px-2 py-1.5 text-xs text-slate-300 hover:bg-surface-border"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? "🌙 Dark" : "☀️ Light"}
          </button>
        </nav>
      </div>
    </header>
  );
}
