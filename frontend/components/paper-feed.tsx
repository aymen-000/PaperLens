"use client"

import { useState, useEffect } from "react"
import { PaperCard } from "@/components/paper-card"
import { Button } from "@/components/ui/button"
import { RefreshCw, Calendar, TrendingUp } from "lucide-react"
import { paperAPI, type Paper } from "@/lib/api"
import { PaperSearch } from "@/components/paper-search"

interface PaperFeedProps {
  onPaperSelect: (paper: Paper) => void
}

export function PaperFeed({ onPaperSelect }: PaperFeedProps) {
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "liked" | "recent">("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [searchFilters, setSearchFilters] = useState<any>(null)

  useEffect(() => {
    loadPapers()
  }, [filter])

  const loadPapers = async () => {
    try {
      setLoading(true)
      const filters = {
        recent: filter === "recent",
        category: filter === "liked" ? "liked" : undefined,
      }
      const response = await paperAPI.getPersonalizedPapers(filters)
      const fetchedPapers = response.papers || response
      setPapers(fetchedPapers)
    } catch (error) {
      console.error("Failed to load papers:", error)
      const mockPapers: Paper[] = [
        {
          id: "1",
          user_id: "123",
          title: "Attention Is All You Need: Revisiting Transformer Architectures for Scientific Text Analysis",
          authors: ["John Smith", "Jane Doe", "Bob Johnson"],
          abstract:
            "We present a comprehensive analysis of transformer architectures applied to scientific text processing...",
          published_at: "2025-01-15",
          categories: ["deep learning"],
          source_url: "http://arxiv.org/pdf/2401.12345",
          liked: false,
        },
        {
          id: "2",
          user_id: "123",
          title: "Quantum Computing Applications in Molecular Dynamics Simulations",
          authors: ["Alice Chen", "David Wilson"],
          abstract:
            "This paper explores the potential of quantum computing algorithms for accelerating molecular dynamics simulations...",
          published_at: "2025-01-14",
          categories: ["quantum physics"],
          source_url: "http://arxiv.org/pdf/2401.12346",
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
        const paper = papers.find((p) => p.id === paperId)
        const categories = paper?.categories || []
        await paperAPI.likePaper(paperId, action === "like", categories)
        setPapers((prev) =>
          prev.map((paper) => (paper.id === paperId ? { ...paper, liked: action === "like" } : paper)),
        )
      } else if (action === "delete") {
        await paperAPI.deletePaper(paperId)
        setPapers((prev) => prev.filter((paper) => paper.id !== paperId))
      }
    } catch (error) {
      console.error(`Failed to ${action} paper:`, error)
    }
  }

  const refreshFeed = async () => {
    try {
      setLoading(true)
      const response = await paperAPI.refreshPapers()
      const refreshedPapers = response.papers || response
      setPapers(refreshedPapers)
    } catch (error) {
      console.error("Failed to refresh papers:", error)
      await loadPapers()
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (query: string, filters: any) => {
    setSearchQuery(query)
    setSearchFilters(filters)
    console.log("Searching for:", query, "with filters:", filters)
  }

  const handleClearSearch = () => {
    setSearchQuery("")
    setSearchFilters(null)
    loadPapers()
  }

  const filteredPapers = papers.filter((paper) => {
    if (filter === "liked" && !paper.liked) return false
    if (filter === "recent" && new Date(paper.published_at) <= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000))
      return false

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchesTitle = paper.title.toLowerCase().includes(query)
      const matchesAuthors = paper.authors.some((author) => author.toLowerCase().includes(query))
      const matchesAbstract = paper.abstract.toLowerCase().includes(query)
      if (!matchesTitle && !matchesAuthors && !matchesAbstract) return false
    }

    if (searchFilters?.categories?.length > 0) {
      const hasMatchingCategory = paper.categories.some((category) =>
        searchFilters.categories.some(
          (filterCat: string) =>
            category.toLowerCase().includes(filterCat.toLowerCase()) ||
            filterCat.toLowerCase().includes(category.toLowerCase()),
        ),
      )
      if (!hasMatchingCategory) return false
    }

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

      <PaperSearch onSearch={handleSearch} onClear={handleClearSearch} />

      <div className="grid gap-4">
        {filteredPapers.map((paper) => (
          <PaperCard key={paper.id} paper={paper} onAction={handlePaperAction} onSelect={() => onPaperSelect(paper)} />
        ))}
      </div>

      {filteredPapers.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            {searchQuery || searchFilters
              ? "No papers found matching your search criteria."
              : "No papers found matching your criteria."}
          </p>
          {(searchQuery || searchFilters) && (
            <Button variant="outline" onClick={handleClearSearch} className="mt-2 bg-transparent">
              Clear Search
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
