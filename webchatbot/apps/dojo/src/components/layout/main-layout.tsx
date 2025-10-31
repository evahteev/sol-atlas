"use client";

import React from "react";
import { ViewerLayout } from "@/components/layout/viewer-layout";

export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <ViewerLayout>
      <div className="flex h-full w-full overflow-hidden bg-background">
        {children}
      </div>
    </ViewerLayout>
  );
}
