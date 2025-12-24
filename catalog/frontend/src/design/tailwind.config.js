const { colors, radius, shadow, spacing, fontSizes } = require('./tokens.ts');

module.exports = {
    theme: {
        extend: {
            colors: {
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
};