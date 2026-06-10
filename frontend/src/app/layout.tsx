import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Office Map",
  description: "Office Printer Status Map",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body style={{ margin: 0, padding: 0, backgroundColor: "#f9fafb" }}>{children}</body>
    </html>
  );
}
