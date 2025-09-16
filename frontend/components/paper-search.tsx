"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Search, X, Filter, ChevronDown, ChevronUp } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface PaperSearchProps {
  onSearch: (query: string, filters: SearchFilters) => void
  onClear: () => void
}

interface SearchFilters {
  categories: string[]
  dateRange: "all" | "week" | "month" | "year"
  authors: string[]
}

const CATEGORIES = [
  "Machine Learning",
  "Deep Learning",
  "Computer Vision",
  "Natural Language Processing",
  "Quantum Computing",
  "Robotics",
  "Artificial Intelligence",
  "Data Science",
  "Bioinformatics",
  "Climate Science",
]

export function PaperSearch({ onSearch, onClear }: PaperSearchProps) {
  const [query, setQuery] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>({
    categories: [],
    dateRange: "all",
    authors: [],
  })

  const handleSearch = () => {
    if (query.trim() || filters.categories.length > 0) {
      onSearch(query, filters)
    }
  }

  const handleClear = () => {
    setQuery("")
    setFilters({
      categories: [],
      dateRange: "all",
      authors: [],
    })
    onClear()
  }

  const toggleCategory = (category: string) => {
    setFilters((prev) => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter((c) => c !== category)
        : [...prev.categories, category],
    }))
  }

  const hasActiveFilters = filters.categories.length > 0 || filters.dateRange !== "all"

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search papers by title, author, or keywords..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10 pr-10"
              />
              {query && (
                <button
                  onClick={() => setQuery("")}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <Button onClick={handleSearch} size="sm" className="flex-shrink-0">
              <Search className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Search</span>
            </Button>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={cn("gap-2 flex-1 sm:flex-none", hasActiveFilters && "border-primary text-primary")}
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
              {hasActiveFilters && (
                <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 text-xs">
                  {filters.categories.length}
                </Badge>
              )}
              {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>

            {hasActiveFilters && (
              <Button variant="outline" size="sm" onClick={handleClear} className="flex-1 sm:flex-none bg-transparent">
                <X className="w-4 h-4 sm:mr-2" />
                <span className="hidden sm:inline">Clear</span>
              </Button>
            )}
          </div>
        </div>

        {showFilters && (
          <div className="border-t pt-4 mt-4 space-y-4">
            <div>
              <h4 className="text-sm font-medium mb-3">Categories</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                {CATEGORIES.map((category) => (
                  <Badge
                    key={category}
                    variant={filters.categories.includes(category) ? "default" : "outline"}
                    className="cursor-pointer hover:bg-primary/10 justify-center text-center py-2 text-xs"
                    onClick={() => toggleCategory(category)}
                  >
                    <span className="truncate">{category}</span>
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium mb-3">Date Range</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { value: "all", label: "All time" },
                  { value: "week", label: "Past week" },
                  { value: "month", label: "Past month" },
                  { value: "year", label: "Past year" },
                ].map((option) => (
                  <Badge
                    key={option.value}
                    variant={filters.dateRange === option.value ? "default" : "outline"}
                    className="cursor-pointer hover:bg-primary/10 justify-center text-center py-2"
                    onClick={() => setFilters((prev) => ({ ...prev, dateRange: option.value as any }))}
                  >
                    {option.label}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={handleClear} className="flex-1 bg-transparent">
                Clear All Filters
              </Button>
              <Button size="sm" onClick={handleSearch} className="flex-1">
                Apply Filters
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
