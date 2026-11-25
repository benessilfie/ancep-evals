export type FlagDecision =
  | "correctly_flagged"
  | "correctly_not_flagged"
  | "missed_flag"
  | "spurious_flag"

export interface FieldVerdict {
  field: string
  declared: boolean
  flagDecision: FlagDecision
  valueCorrect: boolean | null
  provenanceOk: boolean | null
  provenanceDetail: string | null
  detail: string
}

export interface SourceRef {
  document: string
  locator: string
}

export interface Answer {
  status: "extracted" | "flagged"
  value: string
  mode: string
  sources: SourceRef[]
  derived_from: string[]
  reason: string
  recommended_action: string
}

export interface Trial {
  caseId: string
  model: string
  modelLabel: string
  rep: number
  effort: string | null
  passed: boolean
  valueScore: number
  provenanceScore: number
  missedFlags: number
  spuriousFlags: number
  latency: number | null
  outputTokens: number
  fields: FieldVerdict[]
  record: Record<string, Answer | unknown> | null
  notes: string[]
}

export interface Expectation {
  field: string
  outcome: "extracted" | "flagged"
  mode: string | null
  document: string | null
  flagAlsoAcceptable: boolean
  rationale: string
  source: string
}

export interface PacketDocument {
  name: string
  filename: string
  body: string
}

export interface EvalCase {
  id: string
  title: string
  short: string
  kind: "control" | "adversarial"
  exercises: string | null
  corruption: string | null
  pairedWith: string | null
  expectations: Expectation[]
  documents: PacketDocument[]
  trials: Trial[]
}

export interface ModelSummary {
  id: string
  label: string
  passed: number
  total: number
}

export interface EvalData {
  effort: string | null
  reps: number
  models: ModelSummary[]
  cases: EvalCase[]
  totals: { trials: number; passed: number }
}
