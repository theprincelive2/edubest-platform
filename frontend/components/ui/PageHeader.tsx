import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Breadcrumb[];
  action?: React.ReactNode;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  action,
  actions,
  children,
  className,
}: PageHeaderProps) {
  const actionSlot = actions || action;
  return (
    <div className={cn("mb-6 pb-4 border-b border-slate-200 dark:border-slate-800", className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center text-xs text-slate-500 mb-2 space-x-2">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span>/</span>}
              {crumb.href ? (
                <Link href={crumb.href} className="hover:text-blue-600 transition-colors">
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-slate-700 dark:text-slate-300 font-medium">{crumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
          )}
        </div>
        {(actionSlot || children) && (
          <div className="flex items-center gap-2">
            {actionSlot}
            {children}
          </div>
        )}
      </div>
    </div>
  );
}
