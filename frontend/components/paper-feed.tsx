"use client"

import { useState, useEffect } from "react"
import { PaperCard } from "@/components/paper-card"
import { Button } from "@/components/ui/button"
import { RefreshCw, Calendar, TrendingUp } from "lucide-react"
import { paperAPI, type Paper } from "@/lib/api"

interface PaperFeedProps {
  onPaperSelect: (paper: Paper) => void
}

export function PaperFeed({ onPaperSelect }: PaperFeedProps) {
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "liked" | "recent">("all")

  useEffect(() => {
    loadPapers()
  }, [filter])

  const loadPapers = async () => {
    try {
      setLoading(true)
      // Replace this with your FastAPI endpoint call
      const filters = {
        recent: filter === "recent",
        category: filter === "liked" ? "liked" : undefined,
      }
      const fetchedPapers = await paperAPI.getPersonalizedPapers(filters)
      setPapers(fetchedPapers)
    } catch (error) {
      console.error("Failed to load papers:", error)
      // Fallback to mock data if API fails
      const mockPapers: Paper[] = [
        {
          id: "1",
          title: "Attention Is All You Need: Revisiting Transformer Architectures for Scientific Text Analysis",
          authors: ["John Smith", "Jane Doe", "Bob Johnson"],
          abstract:
            "We present a comprehensive analysis of transformer architectures applied to scientific text processing...",
          published_date: "2024-01-15",
          categories: ["Machine Learning"],
          arxiv_id: "arxiv:2401.12345",
          liked: false,
        },
        {
          id: "2",
          title: "Quantum Computing Applications in Molecular Dynamics Simulations",
          authors: ["Alice Chen", "David Wilson"],
          abstract:
            "This paper explores the potential of quantum computing algorithms for accelerating molecular dynamics simulations...",
          published_date: "2024-01-14",
          categories: ["Quantum Physics"],
          arxiv_id: "arxiv:2401.12346",
          liked: true,
        },
      ]
      setPapers(mockPapers)
    } finally {
      setLoading(false)
    }
  }

  const handlePaperAction = async (paperId: string, action: "like" | "dislike" | "delete") => {
    try {
      if (action === "like" || action === "dislike") {
        // Replace with your FastAPI endpoint: POST /api/papers/{id}/like
        await paperAPI.likePaper(paperId, action === "like")
        setPapers((prev) =>
          prev.map((paper) => (paper.id === paperId ? { ...paper, liked: action === "like" } : paper)),
        )
      } else if (action === "delete") {
        // Replace with your FastAPI endpoint: DELETE /api/papers/{id}
        await paperAPI.deletePaper(paperId)
        setPapers((prev) => prev.filter((paper) => paper.id !== paperId))
      }
    } catch (error) {
      console.error(`Failed to ${action} paper:`, error)
      // Handle error (show toast, etc.)
    }
  }

  const refreshFeed = async () => {
    try {
      setLoading(true)
      // Replace with your FastAPI endpoint: POST /api/papers/refresh
      const refreshedPapers = await paperAPI.refreshPapers()
      setPapers(refreshedPapers)
    } catch (error) {
      console.error("Failed to refresh papers:", error)
      // Fallback to reload current papers
      await loadPapers()
    } finally {
      setLoading(false)
    }
  }

  const filteredPapers = papers.filter((paper) => {
    if (filter === "liked") return paper.liked
    if (filter === "recent") return new Date(paper.published_date) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    return true
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading papers...</span>
      </div>
    )
  }

  return (
    <div className="p-4 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-foreground">Today's Papers</h2>
          <p className="text-sm md:text-base text-muted-foreground">
            Personalized recommendations based on your interests
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <div className="flex bg-muted rounded-lg p-1">
            <Button variant={filter === "all" ? "default" : "ghost"} size="sm" onClick={() => setFilter("all")}>
              All
            </Button>
            <Button variant={filter === "recent" ? "default" : "ghost"} size="sm" onClick={() => setFilter("recent")}>
              <Calendar className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Recent</span>
            </Button>
            <Button variant={filter === "liked" ? "default" : "ghost"} size="sm" onClick={() => setFilter("liked")}>
              <TrendingUp className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Liked</span>
            </Button>
          </div>

          <Button variant="outline" size="sm" onClick={refreshFeed} className="w-full sm:w-auto bg-transparent">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4">
        {filteredPapers.map((paper) => (
          <PaperCard key={paper.id} paper={paper} onAction={handlePaperAction} onSelect={() => onPaperSelect(paper)} />
        ))}
      </div>

      {filteredPapers.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No papers found matching your criteria.</p>
        </div>
      )}
    </div>
  )
}
