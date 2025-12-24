'use client';

import { useEffect } from 'react';

/**
 * Bot Embed Component
 * 
 * Loads the bot embed script on client-side.
 * Configure via environment variables:
 * - NEXT_PUBLIC_BOT_API_URL: Bot service API URL (default: http://localhost:8386)
 * - NEXT_PUBLIC_BOT_SITE_ID: Site ID for bot service (default: catalog-001)
 * 
 * Usage:
 * ```tsx
 * import BotEmbed from '@/components/BotEmbed';
 * 
 * export default function Layout() {
 *   return (
 *     <div>
 *       <YourContent />
 *       <BotEmbed />
 *     </div>
 *   );
 * }
 * ```
 */
export default function BotEmbed() {
    useEffect(() => {
        // Only load on client-side
        if (typeof window === 'undefined') {
            return;
        }

        const apiUrl = process.env.NEXT_PUBLIC_BOT_API_URL || 'http://localhost:8386';
        const siteId = process.env.NEXT_PUBLIC_BOT_SITE_ID || 'catalog-001';

        // Check if bot service is reachable (optional pre-check)
        // This is just for better error messages, not required
        fetch(`${apiUrl}/health`, { method: 'GET', mode: 'no-cors' })
            .catch(() => {
                console.warn(
                    `Bot service may not be running at ${apiUrl}. ` +
                    `Please ensure bot service is started: cd bot && docker-compose up -d`
                );
            });

        // Check if script already loaded
        if (document.querySelector(`script[src*="embed.js"]`)) {
            console.log('Bot embed script already loaded.');
            return;
        }

        // Create and load script
        const script = document.createElement('script');
        script.src = `${apiUrl}/embed.js`;
        script.setAttribute('data-site-id', siteId);
        script.setAttribute('data-api-url', apiUrl);
        script.async = true;
        script.defer = true;

        // Handle load
        script.onload = () => {
            console.log('Bot embed script loaded successfully.');
        };

        // Handle error
        script.onerror = (error) => {
            console.error('Failed to load bot embed script', {
                url: `${apiUrl}/embed.js`,
                error,
                message: `Cannot connect to bot service at ${apiUrl}. Please ensure bot service is running.`
            });
        };

        // Append to body
        document.body.appendChild(script);

        // Cleanup on unmount
        return () => {
            const existingScript = document.querySelector(`script[src*="embed.js"]`);
            if (existingScript) {
                existingScript.remove();
                console.log('Bot embed script removed on unmount.');
            }
        };
    }, []);

    return null; // This component doesn't render anything
}

