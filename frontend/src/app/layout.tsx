import type {Metadata} from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Office Map — Printer Monitor",
    description: "Interactive office floor plan with printer monitoring",
    icons: {icon: [{url: '/icon.svg', type: 'image/svg+xml'}]},
};

export const dynamic = "force-dynamic";

export default function RootLayout({children}: { children: React.ReactNode }) {
    const config = {
        apiUrl: process.env.API_URL || "/api",
        pollingInterval: Number(process.env.POLLING_INTERVAL) || 60000,
    };

    const themeVars = {
        "--theme-bg": process.env.THEME_BG || "#0a0a0a",
        "--theme-brand": process.env.THEME_BRAND || "#f59e0b",
        "--theme-brand-hover": process.env.THEME_BRAND_HOVER || "#fbbf24",
        "--theme-brand-dark": process.env.THEME_BRAND_DARK || "#d97706",
        "--theme-brand-muted": (process.env.THEME_BRAND || "#f59e0b") + "33",
    } as React.CSSProperties;

    return (
        <html lang="en" className="h-full antialiased">
        <head>
            <script dangerouslySetInnerHTML={{__html: `window.APP_CONFIG = ${JSON.stringify(config)};`}}/>
        </head>
        <body className="min-h-full flex flex-col font-sans" style={themeVars}>
        {children}
        </body>
        </html>
    );
}