/**
 * Centralized navigation config. Single source of truth for sidebar routes.
 * Each href MUST have a corresponding page at app/{path}/page.tsx.
 */
import {
    LayoutDashboard,
    Cpu,
    BookOpen,
    BarChart3,
    Puzzle,
    Settings,
    MessageSquare,
    Users,
    Package,
    FileText,
    Bot,
    Database,
    Upload,
    LucideIcon,
} from "lucide-react";

export interface NavItem {
    icon: LucideIcon;
    label: string;
    href: string;
    /** Roles that can see this item. Empty = all roles. */
    visibleForRoles?: string[];
}

export interface NavGroup {
    label?: string;
    items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
    {
        label: "VẬN HÀNH (Operations)",
        items: [
            // {
            //     icon: LayoutDashboard,
            //     label: "Tổng quan",
            //     href: "/",
            // },
            {
                icon: MessageSquare,
                label: "Hội thoại",
                href: "/monitor",
            },
            {
                icon: Users,
                label: "Liên hệ (Contacts)",
                href: "/contacts",
            },
        ],
    },
    {
        label: "DỮ LIỆU (Data)",
        items: [
            {
                icon: Package,
                label: "Sản phẩm & Dịch vụ",
                href: "/catalog",
            },
            {
                icon: BookOpen,
                label: "Tri thức AI",
                href: "/knowledge",
            },
            {
                icon: Upload,
                label: "Migration Data",
                href: "/migration",
            },
        ],
    },
    {
        label: "CẤU HÌNH (Configuration)",
        items: [
            {
                icon: Bot,
                label: "Bot & Kịch bản",
                href: "/bots",
            },
            {
                icon: Puzzle,
                label: "Kênh kết nối",
                href: "/integrations",
            },
            {
                icon: Database,
                label: "Tổ chức (Tenants)",
                href: "/tenants",
                visibleForRoles: ["admin", "super_admin"],
            },
        ],
    },
    {
        label: "BÁO CÁO (Analytics)",
        items: [
            {
                icon: BarChart3,
                label: "Hiệu quả Tư vấn",
                href: "/analytics",
            },
            {
                icon: FileText,
                label: "Lịch sử Hoạt động",
                href: "/logs",
            },
        ],
    },
    {
        label: "CÔNG CỤ (Tools)",
        items: [
            {
                icon: Cpu,
                label: "AI Sandbox",
                href: "/studio",
            },
            {
                icon: Database,
                label: "State Debugger",
                href: "/studio/state",
                visibleForRoles: ["admin", "super_admin"],
            },
            {
                icon: Settings,
                label: "Cài đặt chung",
                href: "/settings",
            },
        ],
    },
];

export const DASHBOARD_HREF = "/";
export const SETTINGS_HREF = "/settings";

/** Returns true if user role can see the nav item */
export function canSeeNavItem(item: NavItem, userRole: string | undefined): boolean {
    if (!item.visibleForRoles || item.visibleForRoles.length === 0) {
        return true;
    }
    const role = (userRole || "viewer").toLowerCase();
    return item.visibleForRoles.some((r) => r.toLowerCase() === role);
}
