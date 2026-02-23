import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeInitScript } from "@/lib/theme-init-script";
import { ThemeProvider } from "@/lib/theme-context";
import { QueryProvider } from "@/shared/providers/query-provider";
import { Toaster } from "react-hot-toast";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { SuppressExtensionErrors } from "@/components/SuppressExtensionErrors";
import BotEmbed from "@/components/BotEmbed";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "n8n Market | Buy & Sell n8n Workflows",
    description: "The largest marketplace for n8n templates. Discover, buy, and sell high-quality workflows to save time and scale your operations.",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <head>
                <ThemeInitScript />
            </head>
            <body className={inter.className} suppressHydrationWarning>
                <SuppressExtensionErrors />
                <ErrorBoundary>
                    <QueryProvider>
                        <ThemeProvider>
                            <AuthProvider>
                                {children}
                                <BotEmbed />
                            <Toaster
                                position="top-right"
                                toastOptions={{
                                    duration: 4000,
                                    style: {
                                        background: '#363636',
                                        color: '#fff',
                                    },
                                    success: {
                                        duration: 3000,
                                        iconTheme: {
                                            primary: '#10b981',
                                            secondary: '#fff',
                                        },
                                    },
                                    error: {
                                        duration: 4000,
                                        iconTheme: {
                                            primary: '#ef4444',
                                            secondary: '#fff',
                                        },
                                    },
                                }}
                            />
                            </AuthProvider>
                        </ThemeProvider>
                    </QueryProvider>
                </ErrorBoundary>
            </body>
        </html>
    );
}
