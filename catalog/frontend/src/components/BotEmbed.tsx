'use client';

import { useEffect } from 'react';

/**
 * Bot Embed Component
 * 
 * Loads the bot embed script on client-side.
 * Configure via environment variables:
 * - NEXT_PUBLIC_BOT_API_URL: Bot service API URL (default: http://localhost:8386)
 * - NEXT_PUBLIC_BOT_SITE_ID: Site ID for bot service (default: catalog-001)
 */
export default function BotEmbed() {
    useEffect(() => {
        // Only load on client-side
        if (typeof window === 'undefined') {
            return;
        }

        const apiUrl = process.env.NEXT_PUBLIC_BOT_API_URL || 'http://localhost:8386';
        const siteId = process.env.NEXT_PUBLIC_BOT_SITE_ID || 'catalog-001';

        // Set theme config before loading script
        (window as any).botConfig = {
            siteId: siteId,
            apiUrl: apiUrl,
            theme: {
                primaryColor: '#FF6D3B', // Match catalog primary color
                backgroundColor: '#FFFFFF',
                textColor: '#1A1A1A',
                borderRadius: '12px',
            }
        };

        // Check if widget already exists
        if (document.getElementById('bot-embed-container')) {
            console.log('BotEmbed: Widget already exists, skipping initialization');
            return;
        }

        // Check if script already loaded
        if (document.querySelector(`script[src*="embed.js"]`)) {
            // If script already loaded, try to initialize manually
            if ((window as any).BotEmbed) {
                (window as any).BotEmbed.init({
                    siteId: siteId,
                    apiUrl: apiUrl
                });
            }
            return;
        }

        // Check if bot service is reachable (optional pre-check)
        fetch(`${apiUrl}/health`, { method: 'GET', mode: 'no-cors' })
            .catch(() => {
                console.warn(
                    `Bot service may not be running at ${apiUrl}. ` +
                    `Please ensure bot service is started: cd bot && docker-compose up -d`
                );
            });

        // Create and load script with cache busting
        const script = document.createElement('script');
        const timestamp = Date.now();
        script.src = `${apiUrl}/embed.js?v=${timestamp}`;
        script.setAttribute('data-site-id', siteId);
        script.setAttribute('data-api-url', apiUrl);
        script.async = true;
        script.defer = true;

        // Handle load
        script.onload = () => {
            console.log('Bot embed script loaded successfully');
            // Ensure initialization after script loads
            setTimeout(() => {
                if ((window as any).BotEmbed && (window as any).BotEmbed.init) {
                    (window as any).BotEmbed.init({
                        siteId: siteId,
                        apiUrl: apiUrl
                    });
                }
            }, 100);
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
            }
            // Remove widget if exists
            const widget = document.getElementById('bot-embed-container');
            if (widget) {
                widget.remove();
            }
        };
    }, []);

    return null; // This component doesn't render anything
}

