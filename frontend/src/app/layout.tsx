import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Office Map — Printer Monitor",
    description: "Interactive office floor plan with printer monitoring",
    icons: { icon: [{ url: '/icon.svg', type: 'image/svg+xml' }] },
};

// ВАЖНО: Заставляем Next.js рендерить страницу динамически при каждом запросе,
// чтобы он всегда читал свежие данные из .env, а не кэшировал их при сборке.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
    // 1. Собираем конфиг логики
    const config = {
        apiUrl: process.env.API_URL || "http://localhost:8000/api",
        pollingInterval: Number(process.env.POLLING_INTERVAL) || 60000,
    };

    // 2. Собираем конфиг цветовой темы
    const themeVars = {
        "--theme-bg": process.env.THEME_BG || "#0a0a0a",
        "--theme-brand": process.env.THEME_BRAND || "#f59e0b",
        "--theme-brand-hover": process.env.THEME_BRAND_HOVER || "#fbbf24",
        "--theme-brand-dark": process.env.THEME_BRAND_DARK || "#d97706",
        // Полупрозрачный цвет для фонов кнопок (добавляем прозрачность в HEX)
        "--theme-brand-muted": (process.env.THEME_BRAND || "#f59e0b") + "33",
    } as React.CSSProperties;

    return (
        <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
        <head>
            {/* Инжектим конфиг в глобальный объект window до загрузки React */}
            <script dangerouslySetInnerHTML={{ __html: `window.APP_CONFIG = ${JSON.stringify(config)};` }} />
        </head>
        <body className="min-h-full flex flex-col" style={themeVars}>
        {children}
        </body>
        </html>
    );
}