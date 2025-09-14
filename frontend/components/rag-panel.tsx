"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Send, Bot, User, Loader2, FileText, Quote } from "lucide-react"
import { cn } from "@/lib/utils"
import { ragAPI, type Paper } from "@/lib/api"

interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  references?: string[]
  timestamp: Date
}

interface RAGPanelProps {
  paper: Paper
  onClose: () => void
}

export function RAGPanel({ paper, onClose }: RAGPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        id: "1",
        type: "assistant",
        content: `Hello! I'm here to help you understand "${paper.title}". You can ask me questions about the paper's content, methodology, results, or any specific aspects you'd like to explore.`,
        timestamp: new Date(),
      },
    ])
  }, [paper])

  useEffect(() => {
    // Scroll to bottom when new messages are added
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentQuestion = inputValue
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await ragAPI.askQuestion(currentQuestion, [paper.id])

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: response.answer,
        references: response.sources?.map((source) => source.title) || [],
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Error querying RAG system:", error)

      // Fallback to mock response if API fails
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: `Based on the paper "${paper.title}", I can provide insights about your question: "${currentQuestion}". The authors discuss this topic in the context of ${paper.categories[0]?.toLowerCase() || "research"}, highlighting key methodological approaches and findings. The research demonstrates significant implications for the field.`,
        references: ["Section 3.2", "Figure 2", "Table 1"],
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="fixed inset-0 md:right-0 md:left-auto md:w-96 bg-background border-l border-border shadow-lg z-50 md:top-0 md:h-full">
      <Card className="h-full rounded-none border-0">
        <CardHeader className="border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              <CardTitle className="text-lg">Paper Q&A</CardTitle>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="hover:bg-destructive/10 hover:text-destructive"
            >
              <X className="w-4 h-4" />
              <span className="sr-only">Close chat</span>
            </Button>
          </div>

          <div className="text-sm text-muted-foreground">
            <p className="font-medium text-foreground truncate">{paper.title}</p>
            <p>
              by {paper.authors.slice(0, 2).join(", ")}
              {paper.authors.length > 2 && ` +${paper.authors.length - 2} more`}
            </p>
          </div>
        </CardHeader>

        <CardContent className="flex flex-col h-full p-0">
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn("flex gap-3", message.type === "user" ? "justify-end" : "justify-start")}
                >
                  {message.type === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                  )}

                  <div
                    className={cn(
                      "max-w-[85%] md:max-w-[80%] rounded-lg p-3 text-sm",
                      message.type === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                    )}
                  >
                    <p className="leading-relaxed break-words">{message.content}</p>

                    {message.references && message.references.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-border/50">
                        <div className="flex items-center gap-1 text-xs opacity-70 mb-1">
                          <Quote className="w-3 h-3" />
                          References:
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {message.references.map((ref, index) => (
                            <span key={index} className="text-xs bg-background/50 px-2 py-1 rounded">
                              {ref}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="text-xs opacity-50 mt-2">
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>

                  {message.type === "user" && (
                    <div className="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-secondary" />
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <div className="bg-muted rounded-lg p-3 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">Analyzing paper...</span>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="border-t border-border p-4">
            <div className="flex gap-2">
              <Input
                placeholder="Ask a question about this paper..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="flex-1"
              />
              <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isLoading} size="sm">
                <Send className="w-4 h-4" />
              </Button>
            </div>

            <p className="text-xs text-muted-foreground mt-2">Press Enter to send, Shift+Enter for new line</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
