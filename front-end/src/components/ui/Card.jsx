import { cn } from "../../lib/utils";

export function Card({ children, className }) {
  return (
    <div className={cn(
      "bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 shadow-sm overflow-hidden transition-colors", 
      className
    )}>
      {children}
    </div>
  );
}

export function CardHeader({ title, description, icon: Icon, children }) {
  // If children provided, use custom header layout
  if (children) {
    return (
      <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-900/50">
        {children}
      </div>
    );
  }
  
  // Otherwise use standard layout with title/description/icon
  return (
    <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 flex items-center gap-3 bg-gray-50/50 dark:bg-slate-900/50">
      {Icon && <div className="p-2 bg-blue-100 dark:bg-blue-900/30 text-brand-600 dark:text-brand-400 rounded-lg"><Icon size={20} /></div>}
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        {description && <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>}
      </div>
    </div>
  );
}

export function CardContent({ children, className }) {
  return <div className={cn("p-6", className)}>{children}</div>;
}

// Default export for backward compatibility
export default Card;