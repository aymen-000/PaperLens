"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { BookOpen, Heart, Bell, Settings, Search, TrendingUp } from "lucide-react"

interface SidebarProps {
  activeView: string
  onViewChange: (view: "dashboard" | "interests" | "notifications" | "settings") => void
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: BookOpen },
    { id: "interests", label: "Interests", icon: Heart },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "settings", label: "Settings", icon: Settings },
  ]

  return (
    <div className="w-16 md:w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="p-3 md:p-6">
        <div className="flex items-center gap-2 mb-6 md:mb-8">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Search className="w-4 h-4 text-primary-foreground" />
          </div>
          <h1 className="hidden md:block text-xl font-bold text-sidebar-foreground">PaperLens</h1>
        </div>

        <nav className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            return (
              <Button
                key={item.id}
                variant={activeView === item.id ? "default" : "ghost"}
                className={cn(
                  "w-full h-11 md:justify-start justify-center gap-0 md:gap-3",
                  activeView === item.id
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                )}
                onClick={() => onViewChange(item.id as any)}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden md:inline">{item.label}</span>
              </Button>
            )
          })}
        </nav>
      </div>

      <div className="mt-auto p-3 md:p-6 hidden md:block">
        <div className="bg-sidebar-accent/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-sidebar-accent" />
            <span className="text-sm font-medium text-sidebar-foreground">Today's Stats</span>
          </div>
          <p className="text-xs text-sidebar-foreground/70">12 new papers • 3 liked</p>
        </div>
      </div>
    </div>
  )
}
