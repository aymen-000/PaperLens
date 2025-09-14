import axios from "axios"

const USE_MOCK_DATA = process.env.NODE_ENV === "development" || !process.env.NEXT_PUBLIC_API_URL

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor for auth
api.interceptors.request.use((config) => {
  // TODO: Add your authentication token here
  // const token = localStorage.getItem('token')
  // if (token) {
  //   config.headers.Authorization = `Bearer ${token}`
  // }
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
  title: string
  authors: string[]
  abstract: string
  published_date: string
  arxiv_id?: string
  pdf_url?: string
  categories: string[]
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
    id: "1",
    title: "Attention Is All You Need: Revisiting Transformer Architectures for Scientific Text Analysis",
    authors: ["John Smith", "Jane Doe", "Bob Johnson"],
    abstract:
      "We present a comprehensive analysis of transformer architectures applied to scientific text processing. Our findings demonstrate significant improvements in understanding complex academic literature through attention mechanisms...",
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
      "This paper explores the potential of quantum computing algorithms for accelerating molecular dynamics simulations. We propose novel quantum circuits that can efficiently model complex molecular interactions...",
    published_date: "2024-01-14",
    categories: ["Quantum Physics"],
    arxiv_id: "arxiv:2401.12346",
    liked: true,
  },
  {
    id: "3",
    title: "Neural Network Approaches to Climate Change Prediction Models",
    authors: ["Sarah Martinez", "Michael Brown", "Lisa Wang"],
    abstract:
      "We investigate the application of deep learning techniques to improve climate change prediction accuracy. Our model incorporates multiple data sources and demonstrates superior performance...",
    published_date: "2024-01-13",
    categories: ["Environmental Science"],
    arxiv_id: "arxiv:2401.12347",
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
  // TODO: Replace with your FastAPI endpoint: GET /api/papers
  getPersonalizedPapers: async (filters?: { category?: string; recent?: boolean }) => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      let filteredPapers = [...mockPapers]

      if (filters?.recent) {
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        filteredPapers = filteredPapers.filter((paper) => new Date(paper.published_date) > weekAgo)
      }

      if (filters?.category === "liked") {
        filteredPapers = filteredPapers.filter((paper) => paper.liked)
      }

      return filteredPapers
    }

    const response = await api.get("/api/papers", { params: filters })
    return response.data as Paper[]
  },

  // TODO: Replace with your FastAPI endpoint: POST /api/papers/{id}/like
  likePaper: async (paperId: string, liked: boolean) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(300)
      // Update mock data
      const paper = mockPapers.find((p) => p.id === paperId)
      if (paper) paper.liked = liked
      return { success: true }
    }

    const response = await api.post(`/api/papers/${paperId}/like`, { liked })
    return response.data
  },

  // TODO: Replace with your FastAPI endpoint: DELETE /api/papers/{id}
  deletePaper: async (paperId: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(300)
      const index = mockPapers.findIndex((p) => p.id === paperId)
      if (index > -1) mockPapers.splice(index, 1)
      return { success: true }
    }

    const response = await api.delete(`/api/papers/${paperId}`)
    return response.data
  },

  // TODO: Replace with your FastAPI endpoint: POST /api/papers/refresh
  refreshPapers: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay(1000)
      return [...mockPapers]
    }

    const response = await api.post("/api/papers/refresh")
    return response.data as Paper[]
  },

  // TODO: Replace with your FastAPI endpoint: GET /api/papers/{id}
  getPaperDetails: async (paperId: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return mockPapers.find((p) => p.id === paperId) || mockPapers[0]
    }

    const response = await api.get(`/api/papers/${paperId}`)
    return response.data as Paper
  },
}

// RAG API endpoints
export const ragAPI = {
  // TODO: Replace with your FastAPI endpoint: POST /api/rag/query
  askQuestion: async (question: string, paperIds?: string[]) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(1500)
      return {
        answer: `Based on the research papers, I can provide insights about your question: "${question}". The studies demonstrate significant findings in this area, with methodological approaches that highlight key implications for the field. The evidence suggests strong correlations and potential applications for future research.`,
        sources: [
          { paper_id: paperIds?.[0] || "1", title: "Section 3.2", relevance_score: 0.95 },
          { paper_id: paperIds?.[0] || "1", title: "Figure 2", relevance_score: 0.87 },
          { paper_id: paperIds?.[0] || "1", title: "Table 1", relevance_score: 0.82 },
        ],
        confidence: 0.89,
      } as RAGResponse
    }

    const response = await api.post("/api/rag/query", {
      question,
      paper_ids: paperIds,
    })
    return response.data as RAGResponse
  },

  // TODO: Replace with your FastAPI endpoint: GET /api/rag/history
  getChatHistory: async (sessionId?: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return []
    }

    const response = await api.get("/api/rag/history", {
      params: { session_id: sessionId },
    })
    return response.data
  },
}

// User API endpoints
export const userAPI = {
  // TODO: Replace with your FastAPI endpoint: GET /api/user/profile
  getProfile: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return mockUser
    }

    const response = await api.get("/api/user/profile")
    return response.data as User
  },

  // TODO: Replace with your FastAPI endpoint: PUT /api/user/profile
  updateProfile: async (profileData: Partial<User>) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      Object.assign(mockUser, profileData)
      return mockUser
    }

    const response = await api.put("/api/user/profile", profileData)
    return response.data as User
  },

  // TODO: Replace with your FastAPI endpoint: PUT /api/user/interests
  updateInterests: async (interests: string[]) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      mockUser.research_interests = interests
      return { success: true }
    }

    const response = await api.put("/api/user/interests", { interests })
    return response.data
  },

  // TODO: Replace with your FastAPI endpoint: PUT /api/user/preferences
  updatePreferences: async (preferences: User["ai_preferences"]) => {
    if (USE_MOCK_DATA) {
      await simulateDelay(500)
      mockUser.ai_preferences = preferences
      return { success: true }
    }

    const response = await api.put("/api/user/preferences", preferences)
    return response.data
  },

  // TODO: Replace with your FastAPI endpoint: PUT /api/user/notifications
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

// Auth API endpoints
export const authAPI = {
  // TODO: Replace with your FastAPI endpoint: POST /api/auth/login
  login: async (email: string, password: string) => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return { token: "mock-jwt-token", user: mockUser }
    }

    const response = await api.post("/api/auth/login", { email, password })
    return response.data
  },

  // TODO: Replace with your FastAPI endpoint: POST /api/auth/logout
  logout: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return { success: true }
    }

    const response = await api.post("/api/auth/logout")
    return response.data
  },

  // TODO: Replace with your FastAPI endpoint: GET /api/auth/me
  getCurrentUser: async () => {
    if (USE_MOCK_DATA) {
      await simulateDelay()
      return mockUser
    }

    const response = await api.get("/api/auth/me")
    return response.data as User
  },
}

export default api

/*
TO ENABLE REAL API CALLS:
1. Set NEXT_PUBLIC_API_URL environment variable to your FastAPI backend URL
2. Or change USE_MOCK_DATA to false at the top of this file
3. Replace all TODO comments with your actual FastAPI endpoint implementations

Example environment variable:
NEXT_PUBLIC_API_URL=http://localhost:8000

Your FastAPI endpoints should match these patterns:
- GET /api/papers
- POST /api/papers/{id}/like
- DELETE /api/papers/{id}
- POST /api/papers/refresh
- POST /api/rag/query
- GET /api/user/profile
- PUT /api/user/profile
- PUT /api/user/interests
*/
