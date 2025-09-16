// Authentication utilities
export const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("auth_token")
  }
  return null
}

export const getUserId = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("user_id")
  }
  return null
}

export const isAuthenticated = (): boolean => {
  return !!getAuthToken()
}

export const logout = (): void => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("auth_token")
    localStorage.removeItem("user_id")
    window.location.href = "/login"
  }
}

export const getAuthHeaders = () => {
  const token = getAuthToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}
