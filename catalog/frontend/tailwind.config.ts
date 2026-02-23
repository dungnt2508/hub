import type { Config } from "tailwindcss";
import { colors, radius, shadow, spacing, fontSizes } from "./src/design/tokens";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                background: "var(--background)",
                foreground: "var(--foreground)",
                primary: colors.primary,
                gray50: colors.gray50,
                gray100: colors.gray100,
                gray200: colors.gray200,
                gray600: colors.gray600,
                gray900: colors.gray900,
            },
            borderRadius: {
                sm: radius.sm,
                md: radius.md,
                lg: radius.lg,
            },
            boxShadow: {
                card: shadow.card,
            },
            spacing: {
                card: spacing.card,
                section: spacing.section,
            },
            fontSize: {
                xs: fontSizes.xs,
                sm: fontSizes.sm,
                md: fontSizes.md,
                lg: fontSizes.lg,
                xl: fontSizes.xl,
            },
        },
    },
    plugins: [],
};
export default config;
