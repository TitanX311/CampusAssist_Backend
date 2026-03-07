import type { Metadata } from "next";
import { AuthProvider } from "@/store/AuthContext";
import { ThemeProvider } from "@/providers/ThemeProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Campus Assist — Admin",
  description: "Super admin panel for Campus Assist",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
