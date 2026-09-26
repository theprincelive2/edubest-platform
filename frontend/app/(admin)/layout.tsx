"use client";

/**
 * Admin Portal Layout
 *
 * Provides:
 *  - Collapsible sidebar with grouped navigation items
 *  - Top header with school name, notification bell, and user menu
 *  - Mobile hamburger menu (sidebar slides in as a drawer)
 *  - Active route highlighting
 *  - Role-based nav item visibility
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  BookOpen,
  Calendar,
  ClipboardList,
  FileText,
  UserCheck,
  DollarSign,
  CreditCard,
  Receipt,
  Settings,
  Shield,
  Bell,
  LogOut,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  School,
  User,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useTenantStore } from "@/store/tenantStore";
import { Avatar } from "@/components/ui/Avatar";

/* ── Navigation structure ────────────────────────────────────────── */
interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  requiredPermission?: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    title: "People",
    items: [
      { label: "Students", href: "/admin/students", icon: GraduationCap, requiredPermission: "students.view" },
      { label: "Teachers", href: "/admin/teachers", icon: Users, requiredPermission: "teachers.view" },
      { label: "Classes", href: "/admin/classes", icon: School, requiredPermission: "classes.view" },
      { label: "Subjects", href: "/admin/subjects", icon: BookOpen },
    ],
  },
  {
    title: "Academics",
    items: [
      { label: "Timetable", href: "/admin/timetable", icon: Calendar },
      { label: "Attendance", href: "/admin/attendance", icon: UserCheck, requiredPermission: "attendance.view" },
      { label: "Exams", href: "/admin/exams", icon: ClipboardList, requiredPermission: "exams.view" },
      { label: "Results", href: "/admin/results", icon: FileText, requiredPermission: "results.view" },
    ],
  },
  {
    title: "Finance",
    items: [
      { label: "Finance Overview", href: "/admin/finance", icon: DollarSign, requiredPermission: "finance.view" },
      { label: "Fee Structures", href: "/admin/finance/fees", icon: CreditCard, requiredPermission: "finance.view" },
      { label: "Invoices", href: "/admin/finance/invoices", icon: Receipt, requiredPermission: "finance.view" },
    ],
  },
  {
    title: "System",
    items: [
      { label: "Users", href: "/admin/users", icon: User, requiredPermission: "users.view" },
      { label: "Settings", href: "/admin/settings", icon: Settings, requiredPermission: "settings.manage" },
      { label: "Audit Logs", href: "/admin/audit-logs", icon: Shield, requiredPermission: "audit_logs.view" },
    ],
  },
];

/* ── Sidebar Nav Item ────────────────────────────────────────────── */
function SidebarNavItem({
  item,
  collapsed,
  active,
}: {
  item: NavItem;
  collapsed: boolean;
  active: boolean;
}) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      title={collapsed ? item.label : undefined}
      className={cn(
        "nav-link group relative",
        active && "active",
        collapsed && "justify-center px-2",
      )}
    >
      <Icon className={cn("h-5 w-5 shrink-0", active ? "text-primary-700" : "text-gray-500 group-hover:text-primary-700")} />
      {!collapsed && <span>{item.label}</span>}

      {/* Collapsed tooltip */}
      {collapsed && (
        <span className="pointer-events-none absolute left-full ml-2 whitespace-nowrap rounded-md bg-gray-900 px-2 py-1 text-xs text-white opacity-0 shadow group-hover:opacity-100 transition-opacity z-50">
          {item.label}
        </span>
      )}
    </Link>
  );
}

/* ── Main Layout Component ───────────────────────────────────────── */
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, hasPermission } = useAuthStore();
  const { getSchoolName, getLogoUrl } = useTenantStore();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(href + "/");

  /* ── Sidebar content (shared between desktop and mobile drawer) ─ */
  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      {/* Logo / School name */}
      <div
        className={cn(
          "flex h-16 items-center border-b border-gray-100 px-4",
          sidebarCollapsed ? "justify-center" : "gap-3",
        )}
      >
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-700 text-white font-bold text-sm">
          {getLogoUrl() ? (
            <img src={getLogoUrl()!} alt="School logo" className="h-9 w-9 rounded-lg object-cover" />
          ) : (
            "E"
          )}
        </div>
        {!sidebarCollapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-gray-900">
              {getSchoolName()}
            </p>
            <p className="text-xs text-gray-400">Admin Portal</p>
          </div>
        )}
      </div>

      {/* Nav groups */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-6">
        {NAV_GROUPS.map((group) => {
          // Filter items by permission
          const visibleItems = group.items.filter(
            (item) =>
              !item.requiredPermission ||
              hasPermission(item.requiredPermission),
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.title}>
              {!sidebarCollapsed && (
                <p className="mb-1 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  {group.title}
                </p>
              )}
              <div className="space-y-0.5">
                {visibleItems.map((item) => (
                  <SidebarNavItem
                    key={item.href}
                    item={item}
                    collapsed={sidebarCollapsed}
                    active={isActive(item.href)}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Collapse toggle button (desktop only) */}
      <div className="hidden md:flex border-t border-gray-100 p-2">
        <button
          onClick={() => setSidebarCollapsed((c) => !c)}
          className="flex w-full items-center justify-center rounded-lg p-2 text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-colors"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* ── Desktop Sidebar ──────────────────────────────────────── */}
      <aside
        className={cn(
          "hidden md:flex flex-col border-r border-gray-200 bg-white transition-all duration-300",
          sidebarCollapsed ? "w-16" : "w-64",
        )}
      >
        <SidebarContent />
      </aside>

      {/* ── Mobile Sidebar Drawer ────────────────────────────────── */}
      {mobileSidebarOpen && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 z-40 bg-black/40 md:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
          {/* Drawer */}
          <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl md:hidden">
            <button
              onClick={() => setMobileSidebarOpen(false)}
              className="absolute right-3 top-3 rounded-lg p-1.5 text-gray-400 hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
            <SidebarContent />
          </aside>
        </>
      )}

      {/* ── Main content area ────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header */}
        <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 lg:px-6">
          {/* Left: hamburger + page title */}
          <div className="flex items-center gap-3">
            <button
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 md:hidden"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>

          {/* Right: notification bell + user menu */}
          <div className="flex items-center gap-2">
            {/* Notifications */}
            <button className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors">
              <Bell className="h-5 w-5" />
              {/* Unread badge */}
              <span className="absolute right-1.5 top-1.5 flex h-2 w-2 rounded-full bg-red-500" />
            </button>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen((o) => !o)}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-100 transition-colors"
              >
                <Avatar
                  src={user?.avatar}
                  name={user?.full_name ?? "User"}
                  size="sm"
                />
                <div className="hidden text-left sm:block">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs capitalize text-gray-500">{user?.role}</p>
                </div>
                <ChevronDown className="h-4 w-4 text-gray-400" />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setUserMenuOpen(false)}
                  />
                  <div className="absolute right-0 top-full z-20 mt-1 w-48 rounded-lg border border-gray-100 bg-white py-1 shadow-lg">
                    <Link
                      href="/admin/settings/profile"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <User className="h-4 w-4" />
                      My Profile
                    </Link>
                    <Link
                      href="/admin/settings"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    >
                      <Settings className="h-4 w-4" />
                      Settings
                    </Link>
                    <hr className="my-1 border-gray-100" />
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
