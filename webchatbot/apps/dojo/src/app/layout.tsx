import { Suspense } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { ThemeWrapper } from "@/components/theme-wrapper";
import { MainLayout } from "@/components/layout/main-layout";
import { URLParamsProvider } from "@/contexts/url-params-context";
import { AuthProvider } from "@/contexts/auth-context";
import { LocaleProvider } from "@/contexts/locale-context";
import { UiContextProvider } from "@/contexts/ui-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Demo Viewer by CopilotKit",
  description: "Demo Viewer by CopilotKit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Suspense>
          <LocaleProvider>
            <UiContextProvider>
              <URLParamsProvider>
                <ThemeWrapper>
                  <AuthProvider>
                    <MainLayout>{children}</MainLayout>
                  </AuthProvider>
                </ThemeWrapper>
              </URLParamsProvider>
            </UiContextProvider>
          </LocaleProvider>
        </Suspense>
      </body>
    </html>
  );
}
