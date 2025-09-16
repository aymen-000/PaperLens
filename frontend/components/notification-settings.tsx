"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Mail, MessageCircle, Bell, Clock, Save } from "lucide-react"

export function NotificationSettings() {
  const [emailSettings, setEmailSettings] = useState({
    enabled: true,
    dailyDigest: true,
    weeklyReport: false,
    instantAlerts: false,
    email: "jane.smith@university.edu",
  })

  const [telegramSettings, setTelegramSettings] = useState({
    enabled: false,
    dailyDigest: false,
    instantAlerts: false,
    chatId: "",
  })

  const [generalSettings, setGeneralSettings] = useState({
    browserNotifications: true,
    soundEnabled: false,
    digestTime: "09:00",
  })

  const handleSaveSettings = async () => {
    // TODO: Implement API call to save notification settings to Flask backend
    console.log("Saving notification settings:", {
      email: emailSettings,
      telegram: telegramSettings,
      general: generalSettings,
    })
  }

  const testTelegramConnection = async () => {
    // TODO: Implement API call to test Telegram connection
    console.log("Testing Telegram connection for chat ID:", telegramSettings.chatId)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">Notification Settings</h2>
        <p className="text-muted-foreground">Configure how you want to receive paper updates</p>
      </div>

      {/* Email Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Email Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Enable Email Notifications</Label>
              <p className="text-xs text-muted-foreground">Receive paper updates via email</p>
            </div>
            <Switch
              checked={emailSettings.enabled}
              onCheckedChange={(checked) => setEmailSettings({ ...emailSettings, enabled: checked })}
            />
          </div>

          {emailSettings.enabled && (
            <>
              <div>
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={emailSettings.email}
                  onChange={(e) => setEmailSettings({ ...emailSettings, email: e.target.value })}
                />
              </div>

              <div className="space-y-3 pt-2 border-t border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Daily Digest</Label>
                    <p className="text-xs text-muted-foreground">Daily summary of new papers</p>
                  </div>
                  <Switch
                    checked={emailSettings.dailyDigest}
                    onCheckedChange={(checked) => setEmailSettings({ ...emailSettings, dailyDigest: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Weekly Report</Label>
                    <p className="text-xs text-muted-foreground">Weekly analytics and trends</p>
                  </div>
                  <Switch
                    checked={emailSettings.weeklyReport}
                    onCheckedChange={(checked) => setEmailSettings({ ...emailSettings, weeklyReport: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Instant Alerts</Label>
                    <p className="text-xs text-muted-foreground">Immediate notifications for high-priority papers</p>
                  </div>
                  <Switch
                    checked={emailSettings.instantAlerts}
                    onCheckedChange={(checked) => setEmailSettings({ ...emailSettings, instantAlerts: checked })}
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Telegram Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            Telegram Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Enable Telegram Notifications</Label>
              <p className="text-xs text-muted-foreground">Receive paper updates via Telegram bot</p>
            </div>
            <Switch
              checked={telegramSettings.enabled}
              onCheckedChange={(checked) => setTelegramSettings({ ...telegramSettings, enabled: checked })}
            />
          </div>

          {telegramSettings.enabled && (
            <>
              <div>
                <Label htmlFor="chatId">Telegram Chat ID</Label>
                <div className="flex gap-2">
                  <Input
                    id="chatId"
                    placeholder="Enter your Telegram chat ID"
                    value={telegramSettings.chatId}
                    onChange={(e) => setTelegramSettings({ ...telegramSettings, chatId: e.target.value })}
                  />
                  <Button variant="outline" onClick={testTelegramConnection} disabled={!telegramSettings.chatId}>
                    Test
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Message @PaperLensBot on Telegram to get your chat ID
                </p>
              </div>

              <div className="space-y-3 pt-2 border-t border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Daily Digest</Label>
                    <p className="text-xs text-muted-foreground">Daily summary via Telegram</p>
                  </div>
                  <Switch
                    checked={telegramSettings.dailyDigest}
                    onCheckedChange={(checked) => setTelegramSettings({ ...telegramSettings, dailyDigest: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Instant Alerts</Label>
                    <p className="text-xs text-muted-foreground">Immediate Telegram notifications</p>
                  </div>
                  <Switch
                    checked={telegramSettings.instantAlerts}
                    onCheckedChange={(checked) => setTelegramSettings({ ...telegramSettings, instantAlerts: checked })}
                  />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            General Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Browser Notifications</Label>
              <p className="text-xs text-muted-foreground">Show notifications in your browser</p>
            </div>
            <Switch
              checked={generalSettings.browserNotifications}
              onCheckedChange={(checked) => setGeneralSettings({ ...generalSettings, browserNotifications: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Sound Notifications</Label>
              <p className="text-xs text-muted-foreground">Play sound for new notifications</p>
            </div>
            <Switch
              checked={generalSettings.soundEnabled}
              onCheckedChange={(checked) => setGeneralSettings({ ...generalSettings, soundEnabled: checked })}
            />
          </div>

          <div>
            <Label htmlFor="digestTime" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Daily Digest Time
            </Label>
            <Input
              id="digestTime"
              type="time"
              value={generalSettings.digestTime}
              onChange={(e) => setGeneralSettings({ ...generalSettings, digestTime: e.target.value })}
              className="w-32"
            />
            <p className="text-xs text-muted-foreground mt-1">Time to receive daily digest (your local timezone)</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSaveSettings} className="flex items-center gap-2">
          <Save className="w-4 h-4" />
          Save All Settings
        </Button>
      </div>
    </div>
  )
}
