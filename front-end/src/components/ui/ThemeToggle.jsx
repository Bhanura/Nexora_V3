import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import { cn } from "../../lib/utils";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
      <button
        onClick={() => setTheme("light")}
        className={cn(
          "p-1.5 rounded-md transition-all",
          theme === "light" ? "bg-white dark:bg-slate-600 shadow-sm text-brand-600" : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        )}
        title="Light Mode"
      >
        <Sun size={16} />
      </button>
      <button
        onClick={() => setTheme("dark")}
        className={cn(
          "p-1.5 rounded-md transition-all",
          theme === "dark" ? "bg-white dark:bg-slate-600 shadow-sm text-brand-600" : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        )}
        title="Dark Mode"
      >
        <Moon size={16} />
      </button>
      <button
        onClick={() => setTheme("system")}
        className={cn(
          "p-1.5 rounded-md transition-all",
          theme === "system" ? "bg-white dark:bg-slate-600 shadow-sm text-brand-600" : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        )}
        title="System Default"
      >
        <Monitor size={16} />
      </button>
    </div>
  );
}