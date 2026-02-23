'use client';

import { useEffect } from 'react';

/**
 * Suppress console errors from browser extensions (e.g., runtime.lastError)
 * These errors are harmless and come from extensions trying to communicate
 * with background scripts that may have closed or reloaded.
 */
export function SuppressExtensionErrors() {
    useEffect(() => {
        // Suppress extension-related errors/warnings from browser extensions
        // These are harmless errors from extensions trying to communicate with
        // background scripts that may have closed or reloaded
        const originalError = console.error;
        const originalWarn = console.warn;

        console.error = (...args: any[]) => {
            const message = args[0]?.toString() || '';
            // Suppress extension-related errors
            if (
                message.includes('runtime.lastError') ||
                message.includes('message port closed') ||
                message.includes('Receiving end does not exist') ||
                message.includes('Extension context invalidated') ||
                message.includes('Unchecked runtime.lastError')
            ) {
                return; // Suppress these errors
            }
            originalError.apply(console, args);
        };

        console.warn = (...args: any[]) => {
            const message = args[0]?.toString() || '';
            // Suppress extension-related warnings
            if (
                message.includes('runtime.lastError') ||
                message.includes('message port closed') ||
                message.includes('Receiving end does not exist') ||
                message.includes('Unchecked runtime.lastError')
            ) {
                return; // Suppress these warnings
            }
            originalWarn.apply(console, args);
        };

        // Handle unhandled errors
        const handleError = (event: ErrorEvent) => {
            const message = event.message || '';
            if (
                message.includes('runtime.lastError') ||
                message.includes('message port closed') ||
                message.includes('Receiving end does not exist') ||
                message.includes('Unchecked runtime.lastError')
            ) {
                event.preventDefault();
                return false;
            }
        };

        // Handle unhandled promise rejections
        const handleRejection = (event: PromiseRejectionEvent) => {
            const reason = event.reason?.toString() || '';
            if (
                reason.includes('runtime.lastError') ||
                reason.includes('message port closed') ||
                reason.includes('Receiving end does not exist') ||
                reason.includes('Unchecked runtime.lastError')
            ) {
                event.preventDefault();
                return false;
            }
        };

        window.addEventListener('error', handleError);
        window.addEventListener('unhandledrejection', handleRejection);

        return () => {
            console.error = originalError;
            console.warn = originalWarn;
            window.removeEventListener('error', handleError);
            window.removeEventListener('unhandledrejection', handleRejection);
        };
    }, []);

    return null; // This component doesn't render anything
}

