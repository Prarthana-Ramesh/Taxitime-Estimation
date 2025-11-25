"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, BarChart3, TrendingUp, Network, Plane } from "lucide-react"

type ModelId = "mean" | "rf" | "gnn"

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

  const [outputs, setOutputs] = useState<Record<ModelId, number | null>>({
    mean: null,
    rf: null,
    gnn: null,
  })

  const [loading, setLoading] = useState<Record<ModelId, boolean>>({
    mean: false,
    rf: false,
    gnn: false,
  })

  const handleInputChange = (modelId: ModelId, value: string) => {
    setInputs((prev) => ({
      ...prev,
      [modelId]: value.toUpperCase(),
    }))
  }

  const validatePath = (path: string): boolean => {
    return /^[A-Z0-9-]+$/.test(path) && path.length > 0
  }

  const handleEstimate = async (modelId: ModelId) => {
    const path = inputs[modelId]

    if (!validatePath(path)) {
      alert("Invalid path format. Use format like: RW27-C3-C-F5-F")
      return
    }

    setLoading((prev) => ({
      ...prev,
      [modelId]: true,
    }))

    try {
      await new Promise((resolve) => setTimeout(resolve, 800))

      let estimate = 0
      const baseTime = Math.random() * 10 + 8

      if (modelId === "mean") {
        estimate = Math.round(baseTime)
      } else if (modelId === "rf") {
        estimate = Math.round(baseTime + (Math.random() - 0.5) * 3)
      } else if (modelId === "gnn") {
        estimate = Math.round(baseTime + (Math.random() - 0.5) * 2)
      }

      setOutputs((prev) => ({
        ...prev,
        [modelId]: estimate,
      }))
    } finally {
      setLoading((prev) => ({
        ...prev,
        [modelId]: false,
      }))
    }
  }

  return (
    /* Updated layout with blueprint theme - dark blue background with grid pattern effect */
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 py-12 px-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(0deg,rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

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
                      disabled={!inputs[modelId] || loading[modelId]}
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
                    {outputs[modelId] !== null ? (
                      <div className="space-y-3">
                        <div
                          className={`bg-gradient-to-r ${model.accentColor} rounded-lg p-6 border border-blue-400/30`}
                        >
                          <p className="text-5xl font-bold text-cyan-300 font-mono">{outputs[modelId]}</p>
                          <p className="text-sm text-cyan-200/70 mt-2 font-semibold">minutes</p>
                        </div>
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
