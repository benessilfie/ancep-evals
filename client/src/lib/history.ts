import { useCallback, useEffect, useState } from "react"
import type { Answer } from "@/types"

const KEY = "ancep-evals.runs"
const CAP = 12

export interface PastRun {
  id: string
  at: number
  packetId: string | null
  label: string
  seconds: number
  passed: boolean | null
  raised: number
  blocking: number
  fields: { field: string; answer: Answer }[]
  findings: {
    check: string
    severity: "blocking" | "query" | "note"
    field: string | null
    message: string
  }[]
}

function read(): PastRun[] {
  try {
    const raw = window.localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function useRunHistory() {
  const [runs, setRuns] = useState<PastRun[]>([])

  useEffect(() => setRuns(read()), [])

  const save = useCallback((run: PastRun) => {
    setRuns((prev) => {
      const next = [run, ...prev].slice(0, CAP)
      try {
        window.localStorage.setItem(KEY, JSON.stringify(next))
      } catch {
        /* a private window or a full quota just means no history */
      }
      return next
    })
  }, [])

  const clear = useCallback(() => {
    setRuns([])
    try {
      window.localStorage.removeItem(KEY)
    } catch {
      /* nothing to clear */
    }
  }, [])

  return { runs, save, clear }
}

export function timeAgo(at: number): string {
  const seconds = Math.max(1, Math.round((Date.now() - at) / 1000))
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.round(hours / 24)}d ago`
}
