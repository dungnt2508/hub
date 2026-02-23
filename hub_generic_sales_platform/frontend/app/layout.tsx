import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Assistant Hub 2026",
  description: "Next-gen Hybrid AI Orchestrator Dashboard",
};

import Sidebar from "@/components/Sidebar";
import Providers from "@/components/Providers";
import ProtectedRoute from "@/components/ProtectedRoute";
import { AuthLayout } from "@/components/AuthLayout";
import ToasterProvider from "@/components/ToasterProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-background text-foreground antialiased`}>
        {/* Animated Background Blobs */}
        <div className="fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-600/20 rounded-full blur-[120px] animate-pulse"></div>
          <div className="absolute bottom-[20%] right-[-5%] w-[35%] h-[35%] bg-cyan-600/20 rounded-full blur-[100px] animate-bounce-slow"></div>
          <div className="absolute top-[30%] left-[20%] w-[25%] h-[25%] bg-indigo-600/10 rounded-full blur-[80px]"></div>
        </div>

        <Providers>
          <AuthLayout>
            {children}
          </AuthLayout>
          <ToasterProvider />
        </Providers>
      </body>
    </html>
  );
}
