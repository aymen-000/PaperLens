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
  url: string
  published: string
  like?: boolean
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
    published: "2025-01-15",
    categories: ["deep learning"],
    url: "http://arxiv.org/pdf/2401.12345",
    like: false,
  },
  {
    id: "paper456",
    user_id: "123",
    title: "Quantum Computing Applications in Molecular Dynamics Simulations",
    authors: ["Alice Chen", "David Wilson"],
    abstract:
      "This paper explores the potential of quantum computing algorithms for accelerating molecular dynamics simulations. We propose novel quantum circuits that can efficiently model complex molecular interactions...",
    published: "2025-01-14",
    categories: ["quantum physics"],
    url: "http://arxiv.org/pdf/2401.12346",
    like: true,
  },
  {
    id: "paper789",
    user_id: "123",
    title: "Neural Network Approaches to Climate Change Prediction Models",
    authors: ["Sarah Martinez", "Michael Brown", "Lisa Wang"],
    abstract:
      "We investigate the application of deep learning techniques to improve climate change prediction accuracy. Our model incorporates multiple data sources and demonstrates superior performance...",
    published: "2025-01-13",
    categories: ["machine learning"],
    url: "http://arxiv.org/pdf/2401.12347",
    like: false,
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
// =====================
// Paper API endpoints
// =====================
export const paperAPI = {

  getPersonalizedPapers: async (filters?: { category?: string; recent?: boolean }) => {
    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const response = await api.get(`/api/papers/load_papers?user_id=${userId}`)
    return response.data
  },


  likePaper: async (paperId: string, liked: boolean , categories: string[]) => {
    const userId = getUserId()
    if (!userId) throw new Error("User not authenticated")

    const response = await api.post("/api/user/paper-interaction", {
      user_id: userId,
      paper: { "id": paperId,"categories" : categories },
      interaction: liked ? "LIKE" : "DISLIKE",
    })
    return response.data
  },

  deletePaper: async (paperId: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(300)
      const index = mockPapers.findIndex((p) => p.id === paperId)
      if (index > -1) mockPapers.splice(index, 1)
      return { success: true }
    }

    throw new Error("Delete functionality not implemented in API")
  },

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

