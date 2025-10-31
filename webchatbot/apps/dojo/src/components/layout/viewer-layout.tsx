import React, { useEffect, useState } from "react";
import { CommandPalette } from "@/components/navigation/command-palette";
import { ViewerConfig } from "@/types/feature";
import { cn } from "@/lib/utils";
import { useMobileView } from "@/utils/use-mobile-view";
import { useURLParams } from "@/contexts/url-params-context";
import { Button } from "@/components/ui/button";

interface ViewerLayoutProps extends ViewerConfig {
  className?: string;
  children?: React.ReactNode;
  codeEditor?: React.ReactNode;
  fileTree?: React.ReactNode;
  sidebarHeader?: React.ReactNode;
}

export function ViewerLayout({
  className,
  children,
}: ViewerLayoutProps) {
  const { sidebarHidden } = useURLParams();
  const { isMobile } = useMobileView();

  return (
    <div className={cn("relative flex h-screen overflow-hidden bg-palette-surface-main", className, {
      "p-spacing-2": !isMobile && !sidebarHidden,
    })}>
      <div className="flex flex-1 overflow-hidden z-1">
        <div className="flex flex-1 flex-col overflow-hidden">
          <header className="flex items-center justify-between gap-4 border-b border-border bg-card px-3 py-2">
            <div className="flex items-center gap-2">
              <CommandPaletteTrigger />
            </div>
            <div className="flex items-center gap-3">
              {/* Balance */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-full">
                <span className="text-xs font-medium">0 AIGURU</span>
              </div>
              
              {/* Profile */}
              <ProfileIcon />
            </div>
          </header>
          <main className="flex-1 overflow-auto">
            <div className="h-full">{children}</div>
          </main>
        </div>
      </div>
      {/* Background blur circles - Figma exact specs */}
      {/* Ellipse 1351 */}
      <div className="absolute w-[445.84px] h-[445.84px] left-[1040px] top-[11px] rounded-full z-0" 
           style={{ background: 'rgba(255, 172, 77, 0.2)', filter: 'blur(103.196px)' }} />
      
      {/* Ellipse 1347 */}
      <div className="absolute w-[609.35px] h-[609.35px] left-[1338.97px] top-[624.5px] rounded-full z-0"
           style={{ background: '#C9C9DA', filter: 'blur(103.196px)' }} />
      
      {/* Ellipse 1350 */}
      <div className="absolute w-[609.35px] h-[609.35px] left-[670px] top-[-365px] rounded-full z-0"
           style={{ background: '#C9C9DA', filter: 'blur(103.196px)' }} />
      
      {/* Ellipse 1348 */}
      <div className="absolute w-[609.35px] h-[609.35px] left-[507.87px] top-[702.14px] rounded-full z-0"
           style={{ background: '#F3F3FC', filter: 'blur(103.196px)' }} />
      
      {/* Ellipse 1346 */}
      <div className="absolute w-[445.84px] h-[445.84px] left-[127.91px] top-[331px] rounded-full z-0"
           style={{ background: 'rgba(255, 243, 136, 0.3)', filter: 'blur(103.196px)' }} />
      
      {/* Ellipse 1268 */}
      <div className="absolute w-[445.84px] h-[445.84px] left-[-205px] top-[802.72px] rounded-full z-0"
           style={{ background: 'rgba(255, 172, 77, 0.2)', filter: 'blur(103.196px)' }} />
    </div>
  );
}

function ProfileIcon() {
  // For now, always show guest icon since we don't have access to guest context here
  // The guest context is only available within the BotApiChatPanel component tree
  return (
    <div className="flex items-center">
      <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
        <span className="text-sm">👤</span>
      </div>
    </div>
  );
}

function CommandPaletteTrigger() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(true)}
        className="gap-2 text-xs text-muted-foreground hover:text-foreground"
      >
        <span>🚀</span>
        <kbd className="hidden rounded border border-border bg-muted px-1 py-[1px] text-[10px] font-semibold uppercase text-muted-foreground md:inline-flex">
          ⌘K
        </kbd>
      </Button>
      <CommandPalette open={open} onOpenChange={setOpen} />
    </>
  );
}
