"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Heart,
  HeartOff,
  Trash2,
  ExternalLink,
  Calendar,
  Users,
  MessageSquare,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { Paper } from "@/lib/api"

interface PaperCardProps {
  paper: Paper
  onAction: (paperId: string, action: "like" | "dislike" | "delete") => void
  onSelect: () => void
}

export function PaperCard({ paper, onAction, onSelect }: PaperCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
  }

  const truncateAbstract = (text: string, maxLength = 200) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + "..."
  }

  const getArxivId = () => {
    if (paper.source_url?.includes("arxiv.org")) {
      const match = paper.source_url.match(/(\d{4}\.\d{4,5})/)
      return match ? `arxiv:${match[1]}` : "arXiv"
    }
    return "Paper"
  }

  return (
    <Card className="group hover:shadow-lg transition-all duration-200 border-border bg-card">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-base sm:text-lg font-semibold text-card-foreground leading-tight mb-2 text-balance">
              {paper.title}
            </h3>

            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-muted-foreground mb-2">
              <div className="flex items-center gap-1 min-w-0">
                <Users className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">
                  {paper.authors.slice(0, 2).join(", ")}
                  {paper.authors.length > 2 && ` +${paper.authors.length - 2} more`}
                </span>
              </div>

              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3 flex-shrink-0" />
                <span>{formatDate(paper.published_at)}</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {paper.categories.map((category, index) => (
                <Badge key={index} variant="secondary" className="text-xs capitalize">
                  {category}
                </Badge>
              ))}
              <Badge variant="outline" className="text-xs">
                {getArxivId()}
              </Badge>
            </div>
          </div>

          <div className="flex sm:flex-col gap-2 self-start flex-shrink-0">
            <Button
              variant={paper.liked ? "default" : "outline"}
              size="sm"
              onClick={() => onAction(paper.id, paper.liked ? "dislike" : "like")}
              className={cn(
                "transition-colors flex-1 sm:flex-none min-w-0",
                paper.liked && "bg-secondary hover:bg-secondary/80",
              )}
            >
              {paper.liked ? <Heart className="w-4 h-4 fill-current" /> : <HeartOff className="w-4 h-4" />}
              <span className="ml-2 sm:hidden truncate">{paper.liked ? "Liked" : "Like"}</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => onAction(paper.id, "delete")}
              className="text-destructive hover:text-destructive hover:bg-destructive/10 flex-1 sm:flex-none min-w-0"
            >
              <Trash2 className="w-4 h-4" />
              <span className="ml-2 sm:hidden">Delete</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="mb-4">
          <p className="text-sm text-muted-foreground leading-relaxed break-words">
            {isExpanded ? paper.abstract : truncateAbstract(paper.abstract)}
          </p>

          {paper.abstract.length > 200 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="mt-2 h-auto p-0 text-primary hover:text-primary/80"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4 mr-1" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4 mr-1" />
                  Read more
                </>
              )}
            </Button>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onSelect}
            className="flex items-center justify-center gap-2 bg-transparent"
          >
            <MessageSquare className="w-4 h-4" />
            <span className="truncate">Ask Questions</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground"
            onClick={() => window.open(paper.source_url, "_blank")}
          >
            <ExternalLink className="w-4 h-4" />
            <span className="hidden sm:inline">View Paper</span>
            <span className="sm:hidden truncate">View</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
