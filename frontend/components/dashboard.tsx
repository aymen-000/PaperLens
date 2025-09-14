"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { TopBar } from "@/components/top-bar"
import { PaperFeed } from "@/components/paper-feed"
import { RAGPanel } from "@/components/rag-panel"
import { SettingsPage } from "@/components/settings-page"
import { NotificationSettings } from "@/components/notification-settings"

type ActiveView = "dashboard" | "interests" | "notifications" | "settings"

export function Dashboard() {
  const [activeView, setActiveView] = useState<ActiveView>("dashboard")
  const [selectedPaper, setSelectedPaper] = useState<any>(null)
  const [isRAGOpen, setIsRAGOpen] = useState(false)

  const renderContent = () => {
    switch (activeView) {
      case "dashboard":
        return (
          <PaperFeed
            onPaperSelect={(paper) => {
              setSelectedPaper(paper)
              setIsRAGOpen(true)
            }}
          />
        )
      case "interests":
        return <SettingsPage />
      case "notifications":
        return <NotificationSettings />
      case "settings":
        return <SettingsPage />
      default:
        return <PaperFeed onPaperSelect={() => {}} />
    }
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <div className={`${isRAGOpen ? "hidden md:block" : "block"}`}>
        <Sidebar activeView={activeView} onViewChange={setActiveView} />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className={`${isRAGOpen ? "hidden md:block" : "block"}`}>
          <TopBar />
        </div>

        <main className={`flex-1 overflow-auto ${isRAGOpen ? "hidden md:block" : "block"}`}>{renderContent()}</main>
      </div>

      {isRAGOpen && selectedPaper && (
        <RAGPanel
          paper={selectedPaper}
          onClose={() => {
            setIsRAGOpen(false)
            setSelectedPaper(null)
          }}
        />
      )}
    </div>
  )
}
