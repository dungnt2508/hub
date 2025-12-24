import { UserRole } from '@gsnake/shared-types';

/**
 * Maps user role to their default dashboard/landing route
 * 
 * This allows easy extension for new roles by adding them here.
 * 
 * Example: To add a new "MODERATOR" role:
 * 1. Add MODERATOR to UserRole enum in @gsnake/shared-types
 * 2. Add the route mapping here:
 *    [UserRole.MODERATOR]: '/moderator/dashboard',
 * 3. The redirect will work automatically for login/register
 * 
 * Routes:
 * - USER: Home page (/)
 * - SELLER: Seller dashboard (/seller/dashboard)
 * - ADMIN: Admin dashboard (/admin/dashboard)
 */
export const ROLE_ROUTES: Record<UserRole, string> = {
    [UserRole.USER]: '/',
    [UserRole.SELLER]: '/seller/dashboard',
    [UserRole.ADMIN]: '/admin/dashboard',
};

/**
 * Get the default redirect route for a user based on their role
 * @param role - The user's role
 * @returns The route path to redirect to
 */
export function getRoleRedirectRoute(role: UserRole | string): string {
    // Handle string role values (from API responses)
    const normalizedRole = role as UserRole;
    
    // Check if role exists in mapping
    if (normalizedRole in ROLE_ROUTES) {
        return ROLE_ROUTES[normalizedRole];
    }
    
    // Default fallback route for unknown roles
    console.warn(`Unknown role "${role}", redirecting to home page`);
    return '/';
}

/**
 * Check if a role has a specific dashboard
 * @param role - The user's role
 * @returns true if the role has a dedicated dashboard
 */
export function hasDashboard(role: UserRole | string): boolean {
    const route = getRoleRedirectRoute(role);
    return route !== '/';
}

