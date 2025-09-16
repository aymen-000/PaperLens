import axios from "axios"
import { getAuthHeaders, getUserId } from "./auth"

const USE_MOCK_DATA = process.env.NODE_ENV === "development" && !process.env.NEXT_PUBLIC_API_URL

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const authHeaders = getAuthHeaders()
  config.headers = { ...config.headers, ...authHeaders }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message)
    return Promise.reject(error)
  },
)

// Types for API responses
export interface Paper {
  id: string
  user_id: string
  title: string
  authors: string[]
  abstract: string
  categories: string[]
  source_url: string
  published_at: string
  liked?: boolean
}

export interface User {
  id: string
  name: string
  email: string
  institution?: string
  bio?: string
  research_interests: string[]
  ai_preferences: {
    response_style: string
    detail_level: string
    citation_format: string
  }
  notification_preferences: {
    email_enabled: boolean
    telegram_enabled: boolean
    frequency: string
  }
}

export interface RAGResponse {
  answer: string
  sources: Array<{
    paper_id: string
    title: string
    relevance_score: number
  }>
  confidence: number
}

const mockPapers: Paper[] = [
  {
    id: "paper123",
    user_id: "123",
    title: "Attention Is All You Need: Revisiting Transformer Architectures for Scientific Text Analysis",
    authors: ["John Smith", "Jane Doe", "Bob Johnson"],
    abstract:
      "We present a comprehensive analysis of transformer architectures applied to scientific text processing. Our findings demonstrate significant improvements in understanding complex academic literature through attention mechanisms...",
    published_at: "2025-01-15",
    categories: ["deep learning"],
    source_url: "http://arxiv.org/pdf/2401.12345",
    liked: false,
  },
  {
    id: "paper456",
    user_id: "123",
    title: "Quantum Computing Applications in Molecular Dynamics Simulations",
    authors: ["Alice Chen", "David Wilson"],
    abstract:
      "This paper explores the potential of quantum computing algorithms for accelerating molecular dynamics simulations. We propose novel quantum circuits that can efficiently model complex molecular interactions...",
    published_at: "2025-01-14",
    categories: ["quantum physics"],
    source_url: "http://arxiv.org/pdf/2401.12346",
    liked: true,
  },
  {
    id: "paper789",
    user_id: "123",
    title: "Neural Network Approaches to Climate Change Prediction Models",
    authors: ["Sarah Martinez", "Michael Brown", "Lisa Wang"],
    abstract:
      "We investigate the application of deep learning techniques to improve climate change prediction accuracy. Our model incorporates multiple data sources and demonstrates superior performance...",
    published_at: "2025-01-13",
    categories: ["machine learning"],
    source_url: "http://arxiv.org/pdf/2401.12347",
    liked: false,
  },
]

const mockUser: User = {
  id: "1",
  name: "Dr. Jane Smith",
  email: "jane.smith@university.edu",
  institution: "MIT",
  bio: "Researcher in artificial intelligence and machine learning with focus on scientific applications.",
  research_interests: ["Machine Learning", "Quantum Computing", "Climate Science", "Neuroscience"],
  ai_preferences: {
    response_style: "detailed",
    detail_level: "comprehensive",
    citation_format: "apa",
  },
  notification_preferences: {
    email_enabled: true,
    telegram_enabled: false,
    frequency: "daily",
  },
}

const simulateDelay = (ms = 800) => new Promise((resolve) => setTimeout(resolve, ms))

// Paper API endpoints
export const paperAPI = {
  // Matches: POST /api/papers/load_papers?user_id=<user_id>
  getPersonalizedPapers: async (filters?: { category?: string; recent?: boolean }) => {
    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const response = await api.get(`/api/papers/load_papers?user_id=${userId}`)
    return response.data
  },

  // Matches: POST /api/users/paper-interaction
  likePaper: async (paperId: string, liked: boolean, categories: string[]) => {
    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const response = await api.post("/api/users/paper-interaction", {
      user_id: userId,
      paper: { id: paperId, categories },
      interaction: liked ? "LIKE" : "DISLIKE",
    })
    return response.data
  },

  // Note: Delete functionality not in API docs - keeping as placeholder
  deletePaper: async (paperId: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(300)
      const index = mockPapers.findIndex((p) => p.id === paperId)
      if (index > -1) mockPapers.splice(index, 1)
      return { success: true }
    }

    // TODO: Add delete endpoint to your Flask backend if needed
    throw new Error("Delete functionality not implemented in API")
  },

  // Matches: POST /api/papers/crawl-papers
  refreshPapers: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay(1000)
      return { success: true, papers_count: mockPapers.length, papers: mockPapers }
    }

    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const response = await api.post("/api/papers/crawl-papers", {
      user_id: userId,
    })
    return response.data
  },

  // Health check endpoint
  healthCheck: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay(200)
      return { status: "healthy", message: "Paper Research API is running" }
    }

    const response = await api.get("/api/papers/health")
    return response.data
  },
}

// RAG API endpoints
export const ragAPI = {
  // Matches: POST /api/bot/paper_chat
  askQuestion: async (question: string, paperId?: string, threadId?: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(1500)
      return {
        success: true,
        response: {
          answer: `Based on the research papers, I can provide insights about your question: "${question}". The studies demonstrate significant findings in this area, with methodological approaches that highlight key implications for the field. The evidence suggests strong correlations and potential applications for future research.`,
          sources: [
            { paper_id: paperId || "1", title: "Section 3.2", relevance_score: 0.95 },
            { paper_id: paperId || "1", title: "Figure 2", relevance_score: 0.87 },
            { paper_id: paperId || "1", title: "Table 1", relevance_score: 0.82 },
          ],
        },
      }
    }

    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const response = await api.post("/api/bot/paper_chat", {
      query: question,
      paper_id: paperId,
      user_id: userId,
      thread_id: threadId,
    })
    return response.data
  },

  // Matches: GET /api/bot/chat-history
  getChatHistory: async (paperId?: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return { success: true, count: 0, history: [] }
    }

    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const params = new URLSearchParams({ user_id: userId })
    if (paperId) params.append("paper_id", paperId)

    const response = await api.get(`/api/bot/chat-history?${params.toString()}`)
    return response.data
  },
}

// User API endpoints
export const userAPI = {
  // TODO: Replace with your Flask endpoint: GET /api/user/profile
  getProfile: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return mockUser
    }

    const response = await api.get("/api/user/profile")
    return response.data as User
  },

  // TODO: Replace with your Flask endpoint: PUT /api/user/profile
  updateProfile: async (profileData: Partial<User>) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      Object.assign(mockUser, profileData)
      return mockUser
    }

    const response = await api.put("/api/user/profile", profileData)
    return response.data as User
  },

  // TODO: Replace with your Flask endpoint: PUT /api/user/interests
  updateInterests: async (interests: string[]) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      mockUser.research_interests = interests
      return { success: true }
    }

    const response = await api.put("/api/user/interests", { interests })
    return response.data
  },

  // TODO: Replace with your Flask endpoint: PUT /api/user/preferences
  updatePreferences: async (preferences: User["ai_preferences"]) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      mockUser.ai_preferences = preferences
      return { success: true }
    }

    const response = await api.put("/api/user/preferences", preferences)
    return response.data
  },

  // TODO: Replace with your Flask endpoint: PUT /api/user/notifications
  updateNotificationSettings: async (settings: User["notification_preferences"]) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      mockUser.notification_preferences = settings
      return { success: true }
    }

    const response = await api.put("/api/user/notifications", settings)
    return response.data
  },
}
// ====================
// Auth API endpoints
// ====================
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post("/api/user/login", { email, password })
    console.log("response")
    console.log(response)
    return response.data
  },

  register: async (email: string, password: string, name?: string) => {

    const response = await api.post("/api/user/register", { email, password, name })
    return response.data
  },

  logout: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return { success: true }
    }

    const response = await api.post("/api/user/logout")
    return response.data
  },

  getCurrentUser: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return mockUser
    }

    const response = await api.get("/api/user/me")
    return response.data as User
  },
}

export default api

