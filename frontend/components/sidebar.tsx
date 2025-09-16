"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { BookOpen, Heart, Bell, Settings, Search, TrendingUp, LogOut, User } from "lucide-react"
import { logout, getUserId } from "@/lib/auth"
import { useState, useEffect } from "react"

interface SidebarProps {
  activeView: string
  onViewChange: (view: "dashboard" | "interests" | "notifications" | "settings") => void
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const [userId, setUserId] = useState<string | null>(null)

  useEffect(() => {
    setUserId(getUserId())
  }, [])

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: BookOpen },
    { id: "interests", label: "Interests", icon: Heart },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "settings", label: "Settings", icon: Settings },
  ]

  const handleLogout = () => {
    logout()
  }

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

      <div className="mt-auto p-3 md:p-6">
        <div className="hidden md:block mb-4">
          <div className="bg-sidebar-accent/20 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-sidebar-accent" />
              <span className="text-sm font-medium text-sidebar-foreground">Today's Stats</span>
            </div>
            <p className="text-xs text-sidebar-foreground/70">12 new papers • 3 liked</p>
          </div>

          <div className="flex items-center gap-2 mb-3 p-2 bg-sidebar-accent/10 rounded-lg">
            <div className="w-8 h-8 bg-sidebar-accent rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-sidebar-accent-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">User {userId?.slice(-4) || "****"}</p>
              <p className="text-xs text-sidebar-foreground/70">Researcher</p>
            </div>
          </div>
        </div>

        <Button
          variant="ghost"
          className="w-full h-11 md:justify-start justify-center gap-0 md:gap-3 text-sidebar-foreground hover:bg-destructive/10 hover:text-destructive"
          onClick={handleLogout}
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden md:inline">Logout</span>
        </Button>
      </div>
    </div>
  )
}
