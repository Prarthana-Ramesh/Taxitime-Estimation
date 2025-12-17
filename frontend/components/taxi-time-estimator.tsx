"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, BarChart3, TrendingUp, Network, Plane } from "lucide-react"

type ModelId = "mean" | "rf" | "gnn"

interface PredictionResult {
  success: boolean
  route?: string
  normalized_route?: string
  predictions?: {
    gnn?: number
    rf?: number
    ensemble?: number
  }
  path_stats?: {
    path_length_m: number
    path_length_ft: number
    num_turns: number
    sharpness: number
  }
  error?: string
}

const models = [
  {
    id: "mean",
    title: "Statistical Mean Estimation Model",
    icon: TrendingUp,
    description: "Simple baseline model using historical average taxi times across all routes.",
    features: ["Fast computation", "Historical averages", "Baseline comparison"],
    accentColor: "from-cyan-400/20 to-blue-500/20",
    borderColor: "border-cyan-400/30",
    textColor: "text-cyan-300",
  },
  {
    id: "rf",
    title: "Random Forest Regression Model",
    subtitle: "(Baseline Method)",
    icon: BarChart3,
    description: "Ensemble learning model that captures non-linear relationships in taxi-time patterns.",
    features: ["Ensemble method", "Non-linear patterns", "Feature importance"],
    accentColor: "from-blue-400/20 to-cyan-500/20",
    borderColor: "border-blue-400/30",
    textColor: "text-blue-300",
  },
  {
    id: "gnn",
    title: "Graph Neural Network Estimation Model",
    icon: Network,
    description: "Advanced deep learning model that leverages airport network topology and path sequences.",
    features: ["Graph-based", "Sequence learning", "Spatial relationships"],
    accentColor: "from-indigo-400/20 to-cyan-500/20",
    borderColor: "border-indigo-400/30",
    textColor: "text-indigo-300",
  },
]

export function TaxiTimeEstimator() {
  const [inputs, setInputs] = useState<Record<ModelId, string>>({
    mean: "",
    rf: "",
    gnn: "",
  })

  const [outputs, setOutputs] = useState<Record<ModelId, PredictionResult | null>>({
    mean: null,
    rf: null,
    gnn: null,
  })

  const [loading, setLoading] = useState<Record<ModelId, boolean>>({
    mean: false,
    rf: false,
    gnn: false,
  })

  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "disconnected">("checking")

  useEffect(() => {
    checkBackendStatus()
  }, [])

  const checkBackendStatus = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/health", {
        mode: "cors",
      })
      if (response.ok) {
        setBackendStatus("connected")
      } else {
        setBackendStatus("disconnected")
      }
    } catch (error) {
      setBackendStatus("disconnected")
    }
  }

  const handleInputChange = (modelId: ModelId, value: string) => {
    setInputs((prev) => ({
      ...prev,
      [modelId]: value.toUpperCase(),
    }))
  }

  const validatePath = (path: string): boolean => {
    return /^[A-Z0-9\-,]+$/.test(path) && path.length > 0
  }

  const handleEstimate = async (modelId: ModelId) => {
    const path = inputs[modelId]

    if (!validatePath(path)) {
      alert("Invalid path format. Use format like: RW27-C3-C-F5-F or L-C-H")
      return
    }

    if (backendStatus !== "connected") {
      alert("Backend is not connected. Please ensure the Flask API is running on port 5000.")
      return
    }

    setLoading((prev) => ({
      ...prev,
      [modelId]: true,
    }))

    try {
      const response = await fetch("http://localhost:5000/api/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          route: path,
          model: modelId === "mean" ? "ensemble" : modelId,
        }),
        mode: "cors",
      })

      const data: PredictionResult = await response.json()

      if (data.success) {
        setOutputs((prev) => ({
          ...prev,
          [modelId]: data,
        }))
      } else {
        alert(`Error: ${data.error || "Failed to get prediction"}`)
      }
    } catch (error) {
      alert(`Error connecting to backend: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setLoading((prev) => ({
        ...prev,
        [modelId]: false,
      }))
    }
  }

  const formatTime = (seconds: number | undefined) => {
    if (seconds === undefined || seconds === null) return "N/A"
    const minutes = seconds / 60
    return `${seconds.toFixed(0)}s (${minutes.toFixed(2)}m)`
  }

  const gridBackgroundStyle = {
    backgroundImage: "linear-gradient(0deg,rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)"
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 py-12 px-4 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none bg-[size:40px_40px]" style={gridBackgroundStyle} />

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Plane className="w-10 h-10 text-cyan-400" />
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
              KTEB Airport Taxi-Time Estimation
            </h1>
            <Plane className="w-10 h-10 text-cyan-400 transform scale-x-[-1]" />
          </div>
          <p className="text-lg text-cyan-200/80">
            Compare machine learning models for aircraft taxi-time prediction at Teterboro Airport
          </p>
          {backendStatus === "connected" ? (
            <p className="text-sm text-green-400 mt-2">✅ Backend Connected</p>
          ) : (
            <p className="text-sm text-red-400 mt-2">❌ Backend Disconnected - Make sure Flask API is running</p>
          )}
        </div>

        <Alert className="mb-8 max-w-4xl mx-auto bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border-cyan-400/50">
          <AlertCircle className="h-4 w-4 text-cyan-400" />
          <AlertDescription className="text-cyan-100/90 text-sm">
            Enter an airport path (e.g., <span className="font-mono font-semibold text-cyan-300">RW27-C3-C-F5-F</span>)
            to receive taxi-time estimates from each model.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {models.map((model) => {
            const Icon = model.icon
            const modelId = model.id as ModelId
            const result = outputs[modelId]

            return (
              <div key={model.id} className="flex flex-col group">
                <Card
                  className={`mb-6 h-fit border-2 ${model.borderColor} bg-gradient-to-br from-slate-900/60 to-blue-900/40 backdrop-blur-sm transition-all duration-300 hover:from-slate-900/80 hover:to-blue-900/60`}
                >
                  <CardHeader className="pb-4 border-b border-blue-500/20">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <CardTitle className={`text-lg mb-1 ${model.textColor}`}>{model.title}</CardTitle>
                        {model.subtitle && <p className="text-xs font-semibold text-blue-200/60">{model.subtitle}</p>}
                      </div>
                      <Icon className={`h-6 w-6 ${model.textColor} flex-shrink-0`} />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <CardDescription className="text-blue-100/70 mb-4">{model.description}</CardDescription>
                    <div className="flex flex-wrap gap-2">
                      {model.features.map((feature) => (
                        <span
                          key={feature}
                          className="text-xs bg-blue-500/20 text-cyan-300 px-3 py-1 rounded border border-blue-400/30 font-medium"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className="mb-6 flex-1 border-2 border-blue-400/30 bg-gradient-to-br from-slate-900/60 to-blue-900/40 backdrop-blur-sm">
                  <CardHeader className="pb-4 border-b border-blue-500/20">
                    <CardTitle className="text-base text-cyan-300">Input Path</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 pt-4">
                    <div>
                      <label className="text-sm font-semibold text-cyan-200 mb-2 block">Airport Taxi Path</label>
                      <Input
                        placeholder="e.g., RW27-C3-C-F5-F"
                        value={inputs[modelId]}
                        onChange={(e) => handleInputChange(model.id as ModelId, e.target.value)}
                        className="font-mono uppercase bg-blue-950/40 border-cyan-400/30 text-cyan-100 placeholder:text-blue-200/40"
                      />
                    </div>
                    <Button
                      onClick={() => handleEstimate(model.id as ModelId)}
                      disabled={!inputs[modelId] || loading[modelId] || backendStatus !== "connected"}
                      className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-semibold disabled:opacity-50"
                    >
                      {loading[modelId] ? "Estimating..." : "Estimate Taxi Time"}
                    </Button>
                  </CardContent>
                </Card>

                <Card className="flex-1 border-2 border-blue-400/30 bg-gradient-to-br from-slate-900/60 to-blue-900/40 backdrop-blur-sm">
                  <CardHeader className="pb-4 border-b border-blue-500/20">
                    <CardTitle className="text-base text-cyan-300">Estimated Taxi Time</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    {result && result.success ? (
                      <div className="space-y-4">
                        <div className={`bg-gradient-to-r ${model.accentColor} rounded-lg p-4 border border-blue-400/30`}>
                          <p className="text-sm text-cyan-200/70 mb-2">
                            <strong>Route:</strong> {result.normalized_route}
                          </p>
                          <div className="space-y-2">
                            {modelId === "mean" ? (
                              <>
                                <div>
                                  <p className="text-xs text-cyan-200/60">GNN Prediction</p>
                                  <p className="text-2xl font-bold text-cyan-300 font-mono">
                                    {result.predictions?.gnn ? formatTime(result.predictions.gnn) : "N/A"}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-xs text-cyan-200/60">RF Prediction</p>
                                  <p className="text-2xl font-bold text-cyan-300 font-mono">
                                    {result.predictions?.rf ? formatTime(result.predictions.rf) : "N/A"}
                                  </p>
                                </div>
                                <div className="pt-2 border-t border-cyan-400/20">
                                  <p className="text-xs text-cyan-200/60">Ensemble Average</p>
                                  <p className="text-3xl font-bold text-cyan-300 font-mono">
                                    {result.predictions?.ensemble ? formatTime(result.predictions.ensemble) : "N/A"}
                                  </p>
                                </div>
                              </>
                            ) : modelId === "gnn" ? (
                              <div>
                                <p className="text-xs text-cyan-200/60">GNN Prediction</p>
                                <p className="text-3xl font-bold text-cyan-300 font-mono">
                                  {result.predictions?.gnn ? formatTime(result.predictions.gnn) : "N/A"}
                                </p>
                              </div>
                            ) : (
                              <div>
                                <p className="text-xs text-cyan-200/60">Random Forest Prediction</p>
                                <p className="text-3xl font-bold text-cyan-300 font-mono">
                                  {result.predictions?.rf ? formatTime(result.predictions.rf) : "N/A"}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>

                        {result.path_stats && (
                          <div className="bg-blue-950/40 rounded-lg p-3 border border-blue-400/20 text-xs">
                            <p className="text-cyan-200/70 mb-2">
                              <strong>Path Statistics:</strong>
                            </p>
                            <div className="grid grid-cols-2 gap-2 text-cyan-300/80">
                              <div>
                                <span className="text-cyan-200/60">Length:</span>{" "}
                                {result.path_stats.path_length_m?.toFixed(0)}m ({result.path_stats.path_length_ft?.toFixed(0)}ft)
                              </div>
                              <div>
                                <span className="text-cyan-200/60">Turns:</span> {result.path_stats.num_turns}
                              </div>
                              <div>
                                <span className="text-cyan-200/60">Sharpness:</span> {result.path_stats.sharpness?.toFixed(2)}°
                              </div>
                            </div>
                          </div>
                        )}

                        <button
                          onClick={() =>
                            setOutputs((prev) => ({
                              ...prev,
                              [modelId]: null,
                            }))
                          }
                          className="text-xs text-blue-300/60 hover:text-cyan-300 underline cursor-pointer font-medium transition-colors"
                        >
                          Clear result
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-32 text-blue-300/50">
                        <p className="text-center text-sm">Enter a path and click &quot;Estimate&quot;</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )
          })}
        </div>

        <div className="mt-12 text-center text-sm text-cyan-200/60 max-w-2xl mx-auto">
          <p>
            These models represent different machine learning approaches. Compare their predictions to understand their
            strengths and capabilities in taxi-time estimation.
          </p>
        </div>
      </div>
    </div>
  )
}
