/**
 * Bot Embed Configuration Example
 * 
 * Copy this file and customize for your needs.
 * Set these values BEFORE loading embed.js script.
 */

// Option 1: Set via window.botConfig (before loading embed.js)
window.botConfig = {
    // Required
    siteId: 'your-site-001',                    // Your site ID from bot service
    apiUrl: 'https://bot.yourdomain.com',        // Bot service API URL
    
    // Optional: User identification (for personalized responses)
    userData: {
        userId: 'user-123',                       // Your user ID
        email: 'user@example.com',                // User email
        name: 'John Doe',                        // User name
        // Add any other user data you want to pass
    },
    
    // Optional: Custom theme
    theme: {
        primaryColor: '#FF6B35',                 // Primary color (button, header)
        backgroundColor: '#FFFFFF',               // Chat window background
        textColor: '#1A1A1A',                    // Text color
        borderRadius: '12px',                    // Border radius
        fontFamily: 'Inter, sans-serif',         // Font family
    },
};

// Option 2: Set via script tag attributes (simpler, no JS needed)
// <script 
//   src="https://bot.yourdomain.com/embed.js"
//   data-site-id="your-site-001"
//   data-api-url="https://bot.yourdomain.com"
//   async
//   defer
// ></script>

// Option 3: Environment variables (for React/Next.js)
// NEXT_PUBLIC_BOT_API_URL=https://bot.yourdomain.com
// NEXT_PUBLIC_BOT_SITE_ID=your-site-001

