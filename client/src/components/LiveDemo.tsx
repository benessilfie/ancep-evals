import { useCallback, useEffect, useRef, useState } from "react"
import { BlankRecord } from "@/components/BlankRecord"
import { PacketBrowser } from "@/components/PacketBrowser"
import { RunVerdict, type Graded } from "@/components/RunVerdict"
import { useRunHistory, timeAgo, type PastRun } from "@/lib/history"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { Answer, EvalCase, EvalData } from "@/types"
import { cn } from "@/lib/utils"

const API = import.meta.env.VITE_API ?? "http://127.0.0.1:8000"

interface Finding {
  check: string
  severity: "blocking" | "query" | "note"
  field: string | null
  message: string
}

type Phase = "idle" | "starting" | "reading" | "extracted" | "checking" | "done" | "error"

interface LiveModel {
  id: string
  label: string
  note: string
  available: boolean
}

export function LiveDemo({ data }: { data: EvalData }) {
  const [packetId, setPacketId] = useState(data.cases[0].id)
  const [phase, setPhase] = useState<Phase>("idle")
  const [message, setMessage] = useState<string | null>(null)
  const [fields, setFields] = useState<{ field: string; answer: Answer }[]>([])
  const [findings, setFindings] = useState<Finding[]>([])
  const [meta, setMeta] = useState<{ seconds?: number; tokens?: number }>({})
  const [files, setFiles] = useState<FileList | null>(null)
  const [pane, setPane] = useState<"packet" | "record">("packet")
  const [graded, setGraded] = useState<Graded | null>(null)
  const [uploaded, setUploaded] = useState(false)
  const source = useRef<EventSource | null>(null)
  const collected = useRef<{ fields: typeof fields; findings: Finding[] }>({
    fields: [],
    findings: [],
  })
  const { runs, save } = useRunHistory()
  const [models, setModels] = useState<LiveModel[]>([])
  const [model, setModel] = useState<string | null>(null)

  useEffect(() => () => source.current?.close(), [])

  const loadModels = useCallback(() => {
    fetch(`${API}/api/health`)
      .then((r) => r.json())
      .then((d) => {
        setModels(d.models ?? [])
        setModel((m) => m ?? d.default ?? null)
      })
      .catch(() => setModels([]))
  }, [])

  useEffect(loadModels, [loadModels])

  const start = async () => {
    source.current?.close()
    setFields([])
    setFindings([])
    setMeta({})
    setMessage(null)
    setGraded(null)
    collected.current = { fields: [], findings: [] }
    setUploaded(Boolean(files && files.length > 0))
    setPhase("starting")
    setPane("record")

    const body = new FormData()
    const uploadedNow = Boolean(files && files.length > 0)
    const chosenLabel = models.find((m) => m.id === model)?.label ?? "Haiku 5.5"
    if (files && files.length > 0) {
      for (const file of Array.from(files)) body.append("files", file)
    } else {
      body.append("packet_id", packetId)
    }
    if (model) body.append("model", model)

    let runId: string
    try {
      const res = await fetch(`${API}/api/runs`, { method: "POST", body })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        setMessage(detail.detail ?? `the server said ${res.status}`)
        setPhase("error")
        return
      }
      runId = (await res.json()).run_id
    } catch {
      setMessage(
        `Cannot reach the eval service at ${API}. Start it with: uv run uvicorn submission_evals.server:app --port 8000`
      )
      setPhase("error")
      return
    }

    const es = new EventSource(`${API}/api/runs/${runId}/events`)
    source.current = es
    es.addEventListener("stage", (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      setPhase(d.stage === "received" ? "reading" : d.stage)
      if (d.seconds) setMeta({ seconds: d.seconds, tokens: d.tokens })
    })
    es.addEventListener("field", (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      collected.current.fields.push(d)
      setFields((prev) => [...prev, d])
    })
    es.addEventListener("finding", (e) => {
      const f = JSON.parse((e as MessageEvent).data)
      collected.current.findings.push(f)
      setFindings((prev) => [...prev, f])
    })
    es.addEventListener("done", (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      setMeta((m) => ({ ...m, seconds: d.seconds }))
      setGraded(d.graded ?? null)
      setPhase("done")
      loadModels()
      const taken = collected.current
      save({
        id: runId,
        at: Date.now(),
        packetId: uploadedNow ? null : packetId,
        label: uploadedNow
          ? "your documents"
          : (data.cases.find((c) => c.id === packetId)?.short ?? packetId),
        seconds: d.seconds,
        model: chosenLabel,
        passed: d.graded ? d.graded.passed : null,
        raised: taken.fields.filter((f) => f.answer.status === "flagged").length,
        blocking: d.blocking ?? 0,
        fields: taken.fields,
        findings: taken.findings,
      })
      es.close()
    })
    es.addEventListener("error", (e) => {
      const raw = (e as MessageEvent).data
      setMessage(raw ? JSON.parse(raw).message : "the stream dropped")
      setPhase("error")
      es.close()
    })
  }

  const running = phase === "starting" || phase === "reading" || phase === "checking"
  const answers = new Map(fields.map((f) => [f.field, f.answer]))
  const selectedCase: EvalCase | undefined = data.cases.find((c) => c.id === packetId)
  const chosen = models.find((m) => m.id === model)

  const restore = (run: PastRun) => {
    source.current?.close()
    setFields(run.fields)
    setFindings(run.findings)
    setGraded(run.passed === null ? null : { passed: run.passed, valueScore: 0, provenanceScore: 0 })
    setUploaded(run.packetId === null)
    if (run.packetId) setPacketId(run.packetId)
    setMeta({ seconds: run.seconds })
    setMessage(null)
    setPhase("done")
    setPane("record")
  }

  return (
    <div className="flex min-h-0 flex-1 overflow-hidden">
      <aside className="w-[22rem] shrink-0 overflow-y-auto border-r border-rule bg-paper-sunk/40 px-5 py-5">
        <h2 className="text-[0.9375rem] font-semibold">Run one yourself</h2>
        <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-soft">
          Pick a packet and a model, read what is in the packet, then send it over. The
          model fills in the record and the checks run against the documents it was given,
          so an upload of your own works the same way.
        </p>

        {models.length > 0 && (
          <div className="mt-5">
            <span className="field-label">model</span>
            <div className="mt-1.5 grid grid-cols-3 gap-1.5">
              {models.map((m) => {
                const on = m.id === model
                return (
                  <button
                    key={m.id}
                    type="button"
                    disabled={running || !m.available}
                    onClick={() => setModel(m.id)}
                    title={m.available ? m.note : "not available right now"}
                    className={cn(
                      "pressable rounded-field border px-2 py-2.5 text-center text-[0.8125rem] font-medium transition-colors",
                      on
                        ? "border-ink bg-ink text-paper"
                        : "border-rule bg-white hover:border-ink-faint",
                      !m.available && "opacity-40"
                    )}
                  >
                    {m.label.replace(" 5.5", "")}
                  </button>
                )
              })}
            </div>
            {chosen && (
              <p className="mt-2 text-[0.75rem] text-ink-faint">{chosen.note}</p>
            )}
          </div>
        )}

        <div className="mt-5">
          <label className="field-label" htmlFor="packet">packet</label>
          <Select value={packetId} onValueChange={setPacketId} disabled={running}>
            <SelectTrigger
              id="packet"
              className="pressable mt-1.5 w-full rounded-field border border-rule bg-white px-2.5 py-2 text-left text-[0.8125rem]"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent
              position="popper"
              sideOffset={4}
              className="pop z-50 max-h-[24rem] w-[var(--radix-select-trigger-width)] overflow-y-auto rounded-field border border-rule bg-white p-1 shadow-[0_10px_30px_-14px_rgba(22,23,26,0.4)]"
            >
              {data.cases.map((c) => (
                <SelectItem
                  key={c.id}
                  value={c.id}
                  className="cursor-pointer rounded-field px-2.5 py-2 text-[0.8125rem] outline-none focus:bg-paper-sunk data-[state=checked]:bg-carbon-wash data-[state=checked]:font-medium data-[state=checked]:text-carbon data-[state=checked]:shadow-[inset_2px_0_0_var(--color-carbon)]"
                >
                  <span className="flex items-baseline gap-2">
                    <span className="font-mono text-[0.6875rem] text-ink-faint">
                      {c.id.slice(0, 2)}
                    </span>
                    <span className="leading-snug">{c.short || c.title}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="mt-5">
          <label className="field-label" htmlFor="upload">
            or upload your own
          </label>
          <input
            id="upload"
            type="file"
            multiple
            disabled={running}
            onChange={(e) => setFiles(e.target.files)}
            className="mt-1.5 w-full text-[0.75rem] file:mr-2 file:rounded-field file:border file:border-rule file:bg-white file:px-2 file:py-1 file:text-[0.75rem]"
          />
          <p className="mt-1.5 text-[0.6875rem] leading-relaxed text-ink-faint">
            Filenames must match the document they are, for example application.txt,
            loss_run_a.csv, sov.csv.
          </p>
          {files && files.length > 0 && (
            <button
              type="button"
              onClick={() => setFiles(null)}
              className="mt-1 font-mono text-micro text-carbon hover:underline"
            >
              clear {files.length} file{files.length === 1 ? "" : "s"}
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={start}
          disabled={running}
          className="pressable mt-6 w-full rounded-control bg-ink px-4 py-3 text-[0.9375rem] font-medium text-paper transition-colors hover:bg-ink-lift disabled:opacity-60"
        >
          {running ? "running…" : "Run the checks"}
        </button>

        <p className="mt-3 text-[0.6875rem] leading-relaxed text-ink-faint">
          Runs are rate limited.
        </p>

        {runs.length > 0 && (
          <div className="mt-7 border-t border-rule pt-5">
            <div className="field-label">your runs</div>
            <ul className="mt-2 -mx-1.5">
              {runs.map((run) => (
                <li key={run.id}>
                  <button
                    type="button"
                    onClick={() => restore(run)}
                    className="pressable flex w-full items-baseline gap-2.5 rounded-field px-1.5 py-1.5 text-left transition-colors hover:bg-white"
                  >
                    <span
                      className={cn(
                        "shrink-0 font-mono text-[0.625rem]",
                        run.passed === null
                          ? "text-ink-faint"
                          : run.passed
                            ? "text-seal"
                            : "text-stamp"
                      )}
                    >
                      {run.passed === null ? "yours" : run.passed ? "right" : "wrong"}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-[0.8125rem]">
                      {run.label}
                      {run.model && (
                        <span className="ml-1.5 font-mono text-[0.625rem] text-ink-faint">
                          {run.model.replace(" 5.5", "")}
                        </span>
                      )}
                    </span>
                    <span className="shrink-0 font-mono text-[0.625rem] text-ink-faint">
                      {timeAgo(run.at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>

      <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex shrink-0 items-center gap-1 border-b border-rule px-5 pt-2">
          {(["packet", "record"] as const).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setPane(key)}
              className={cn(
                "px-2 py-1.5 text-[0.75rem] [border-style:solid] [border-width:0_0_2px_0]",
                pane === key
                  ? "[border-bottom-color:var(--color-carbon)] font-medium text-carbon"
                  : "[border-bottom-color:transparent] text-ink-soft hover:text-ink"
              )}
            >
              {key === "packet" ? "what it was given" : "how it did"}
            </button>
          ))}
        </div>

        {pane === "packet" && selectedCase && !files?.length ? (
          <PacketBrowser key={selectedCase.id} evalCase={selectedCase} />
        ) : (
          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
            <Progress phase={phase} meta={meta} count={fields.length} />

            {message && (
              <div className="mt-4 border-l-2 border-stamp bg-stamp-wash px-4 py-3 text-[0.875rem] leading-relaxed text-stamp">
                {message}
              </div>
            )}

            {phase === "done" && (
              <div className="mt-5">
                <RunVerdict
                  evalCase={uploaded ? undefined : selectedCase}
                  graded={graded}
                  findings={findings}
                  answers={answers}
                  uploaded={uploaded}
                />
              </div>
            )}

            <div className="mt-6">
              <BlankRecord answers={answers} running={running} />
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

const STAGES: { key: Phase; label: string }[] = [
  { key: "reading", label: "reading the documents" },
  { key: "extracted", label: "record produced" },
  { key: "checking", label: "checking it against the documents" },
  { key: "done", label: "done" },
]

function Progress({
  phase,
  meta,
  count,
}: {
  phase: Phase
  meta: { seconds?: number; tokens?: number }
  count: number
}) {
  if (phase === "idle") {
    return (
      <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
        Nothing running. Pick a packet on the left and press run, or drop in your own
        documents.
      </p>
    )
  }
  const reached = STAGES.findIndex((s) => s.key === phase)
  return (
    <div>
      <ol className="flex flex-wrap gap-x-6 gap-y-2">
        {STAGES.map((stage, i) => {
          const state = phase === "error" ? "idle" : i < reached ? "past" : i === reached ? "now" : "idle"
          return (
            <li key={stage.key} className="flex items-center gap-2">
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  state === "past" && "bg-seal",
                  state === "now" && "animate-pulse bg-carbon",
                  state === "idle" && "bg-rule"
                )}
              />
              <span
                className={cn(
                  "text-[0.8125rem]",
                  state === "idle" ? "text-ink-faint" : "text-ink"
                )}
              >
                {stage.label}
              </span>
            </li>
          )
        })}
      </ol>
      <p className="mt-2 font-mono text-micro text-ink-faint">
        {meta.seconds ? `${meta.seconds}s` : "waiting on the model"}
        {meta.tokens ? ` · ${meta.tokens.toLocaleString()} tokens` : ""}
        {count > 0 ? ` · ${count} fields` : ""}
      </p>
    </div>
  )
}
