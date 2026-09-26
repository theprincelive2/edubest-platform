import React from "react";
import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: React.ElementType;
  iconBg?: string;
  iconColor?: string;
  trend?: {
    value: number;
    direction?: "up" | "down";
    positive?: boolean;
    label?: string;
  };
  description?: string;
  className?: string;
}

export function StatsCard({
  label,
  value,
  icon: Icon,
  iconBg = "bg-blue-50 dark:bg-blue-950",
  iconColor = "text-blue-600 dark:text-blue-400",
  trend,
  description,
  className,
}: StatsCardProps) {
  const isPositive =
    trend?.positive !== undefined
      ? trend.positive
      : trend?.direction === "up";

  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
        {Icon && (
          <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", iconBg, iconColor)}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              "inline-flex items-center text-xs font-semibold",
              isPositive ? "text-emerald-600" : "text-rose-600"
            )}
          >
            {isPositive ? (
              <ArrowUpRight className="h-3.5 w-3.5 mr-0.5" />
            ) : (
              <ArrowDownRight className="h-3.5 w-3.5 mr-0.5" />
            )}
            {Math.abs(trend.value)}%
            {trend.label && <span className="ml-1 text-slate-400 font-normal">{trend.label}</span>}
          </span>
        )}
      </div>
      {description && (
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{description}</p>
      )}
    </div>
  );
}
