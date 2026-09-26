import React from "react";
import { cn, getInitials } from "@/lib/utils";

interface AvatarProps {
  src?: string | null;
  name?: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

export function Avatar({ src, name, size = "md", className }: AvatarProps) {
  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-12 h-12 text-base",
    xl: "w-16 h-16 text-lg",
  };

  if (src) {
    return (
      <img
        src={src}
        alt={name || "Avatar"}
        className={cn(
          "rounded-full object-cover border border-slate-200 dark:border-slate-700",
          sizeClasses[size],
          className
        )}
      />
    );
  }

  const initials = name ? getInitials(name) : "?";

  return (
    <div
      className={cn(
        "rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 font-semibold flex items-center justify-center border border-blue-200 dark:border-blue-800",
        sizeClasses[size],
        className
      )}
    >
      {initials}
    </div>
  );
}
