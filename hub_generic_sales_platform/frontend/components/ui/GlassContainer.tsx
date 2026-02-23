"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassContainerProps {
    children: ReactNode;
    className?: string;
    glow?: boolean;
}

export default function GlassContainer({ children, className, glow = false }: GlassContainerProps) {
    return (
        <div className={cn(
            "glass-effect rounded-2xl overflow-hidden transition-all duration-300",
            glow && "glass-glow",
            className
        )}>
            {children}
        </div>
    );
}
