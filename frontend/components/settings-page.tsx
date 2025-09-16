"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Plus, X, Save, Brain, Tags, User, Loader2 } from "lucide-react"
import { userAPI } from "@/lib/api"

export function SettingsPage() {
  const [interests, setInterests] = useState<string[]>([])
  const [newInterest, setNewInterest] = useState("")
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    institution: "",
    bio: "",
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadUserData()
  }, [])

  const loadUserData = async () => {
    try {
      setLoading(true)
      // Replace with your Flask endpoint: GET /api/user/profile
      const userData = await userAPI.getProfile()

      setProfile({
        name: userData.name,
        email: userData.email,
        institution: userData.institution || "",
        bio: userData.bio || "",
      })
      setInterests(userData.research_interests || [])
    } catch (error) {
      console.error("Failed to load user data:", error)
      // Fallback to mock data if API fails
      setProfile({
        name: "Dr. Jane Smith",
        email: "jane.smith@university.edu",
        institution: "MIT",
        bio: "Researcher in artificial intelligence and machine learning with focus on scientific applications.",
      })
      setInterests(["Machine Learning", "Quantum Computing", "Climate Science", "Neuroscience"])
    } finally {
      setLoading(false)
    }
  }

  const addInterest = () => {
    if (newInterest.trim() && !interests.includes(newInterest.trim())) {
      setInterests([...interests, newInterest.trim()])
      setNewInterest("")
    }
  }

  const removeInterest = (interest: string) => {
    setInterests(interests.filter((i) => i !== interest))
  }

  const handleSaveProfile = async () => {
    try {
      setSaving(true)
      // Replace with your Flask endpoint: PUT /api/user/profile
      await userAPI.updateProfile(profile)
      // Show success message (you can add toast notification here)
      console.log("Profile saved successfully")
    } catch (error) {
      console.error("Failed to save profile:", error)
      // Handle error (show error message)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveInterests = async () => {
    try {
      setSaving(true)
      // Replace with your Flask endpoint: PUT /api/user/interests
      await userAPI.updateInterests(interests)
      // Show success message (you can add toast notification here)
      console.log("Interests saved successfully")
    } catch (error) {
      console.error("Failed to save interests:", error)
      // Handle error (show error message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading settings...</span>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">Settings & Preferences</h2>
        <p className="text-muted-foreground">Customize your PaperLens experience</p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            Profile Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="institution">Institution</Label>
            <Input
              id="institution"
              value={profile.institution}
              onChange={(e) => setProfile({ ...profile, institution: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              rows={3}
            />
          </div>

          <Button onClick={handleSaveProfile} disabled={saving} className="w-full md:w-auto">
            {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Save Profile
          </Button>
        </CardContent>
      </Card>

      {/* Research Interests */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Research Interests
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Add your research interests to get personalized paper recommendations
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Add a research interest..."
              value={newInterest}
              onChange={(e) => setNewInterest(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && addInterest()}
            />
            <Button onClick={addInterest} disabled={!newInterest.trim()}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {interests.map((interest) => (
              <Badge key={interest} variant="secondary" className="flex items-center gap-1 px-3 py-1">
                <Tags className="w-3 h-3" />
                {interest}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-auto p-0 ml-1 hover:bg-transparent"
                  onClick={() => removeInterest(interest)}
                >
                  <X className="w-3 h-3" />
                </Button>
              </Badge>
            ))}
          </div>

          {interests.length === 0 && (
            <p className="text-sm text-muted-foreground italic">
              No interests added yet. Add some to get personalized recommendations!
            </p>
          )}

          <Button onClick={handleSaveInterests} disabled={saving} className="w-full md:w-auto">
            {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Save Interests
          </Button>
        </CardContent>
      </Card>

      {/* AI Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            AI Assistant Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-medium">Detailed Explanations</Label>
                <p className="text-xs text-muted-foreground">Get comprehensive answers with references</p>
              </div>
              <Button variant="outline" size="sm">
                Enabled
              </Button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-medium">Quick Summaries</Label>
                <p className="text-xs text-muted-foreground">Prefer concise responses</p>
              </div>
              <Button variant="outline" size="sm">
                Disabled
              </Button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-medium">Visual Highlights</Label>
                <p className="text-xs text-muted-foreground">Highlight referenced text in papers</p>
              </div>
              <Button variant="outline" size="sm">
                Enabled
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
