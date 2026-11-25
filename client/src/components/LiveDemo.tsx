import { useEffect, useRef, useState } from "react"
import { BlankRecord } from "@/components/BlankRecord"
import { PacketBrowser } from "@/components/PacketBrowser"
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

export function LiveDemo({ data }: { data: EvalData }) {
  const [packetId, setPacketId] = useState(data.cases[0].id)
  const [phase, setPhase] = useState<Phase>("idle")
  const [message, setMessage] = useState<string | null>(null)
  const [fields, setFields] = useState<{ field: string; answer: Answer }[]>([])
  const [findings, setFindings] = useState<Finding[]>([])
  const [meta, setMeta] = useState<{ seconds?: number; tokens?: number }>({})
  const [files, setFiles] = useState<FileList | null>(null)
  const [pane, setPane] = useState<"packet" | "record">("packet")
  const source = useRef<EventSource | null>(null)

  useEffect(() => () => source.current?.close(), [])

  const start = async () => {
    source.current?.close()
    setFields([])
    setFindings([])
    setMeta({})
    setMessage(null)
    setPhase("starting")
    setPane("record")

    const body = new FormData()
    if (files && files.length > 0) {
      for (const file of Array.from(files)) body.append("files", file)
    } else {
      body.append("packet_id", packetId)
    }

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
      setFields((prev) => [...prev, d])
    })
    es.addEventListener("finding", (e) => {
      setFindings((prev) => [...prev, JSON.parse((e as MessageEvent).data)])
    })
    es.addEventListener("done", (e) => {
      const d = JSON.parse((e as MessageEvent).data)
      setMeta((m) => ({ ...m, seconds: d.seconds }))
      setPhase("done")
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
  const blocking = findings.filter((f) => f.severity === "blocking")

  return (
    <div className="flex min-h-0 flex-1 overflow-hidden">
      <aside className="w-[22rem] shrink-0 overflow-y-auto border-r border-rule bg-paper-sunk/40 px-5 py-5">
        <h2 className="text-[0.9375rem] font-semibold">Run one yourself</h2>
        <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-soft">
          Pick a packet or upload your own documents. It goes to {" "}
          <span className="font-mono text-[0.75rem]">claude-haiku-5-5</span> and comes back
          with a record, then the checks run against the documents you supplied. No ground
          truth needed.
        </p>

        <div className="mt-5">
          <label className="field-label" htmlFor="packet">
            packet
          </label>
          <select
            id="packet"
            value={packetId}
            disabled={running || !!files?.length}
            onChange={(e) => setPacketId(e.target.value)}
            className="mt-1.5 w-full rounded-field border border-rule bg-white px-2.5 py-2 text-[0.8125rem] disabled:opacity-50"
          >
            {data.cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id.slice(0, 2)} · {c.title}
              </option>
            ))}
          </select>
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
          className="mt-6 w-full rounded-control bg-ink px-4 py-3 text-[0.9375rem] font-medium text-paper transition-colors hover:bg-carbon disabled:opacity-60"
        >
          {running ? "running…" : "Run the checks"}
        </button>

        <p className="mt-3 text-[0.6875rem] leading-relaxed text-ink-faint">
          About half a cent a run, rate limited per address.
        </p>
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
              {key === "packet" ? "the documents" : "the record"}
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

            {findings.length > 0 && (
              <section className="mt-6">
                <h3 className="text-[0.9375rem] font-semibold">
                  {blocking.length > 0
                    ? `${blocking.length} thing${blocking.length === 1 ? "" : "s"} a human needs to see`
                    : "Nothing blocking"}
                </h3>
                <ul className="mt-3 space-y-2">
                  {findings.map((f, i) => (
                    <li
                      key={i}
                      className={cn(
                        "border-l-2 px-4 py-2.5",
                        f.severity === "blocking"
                          ? "border-stamp bg-stamp-wash"
                          : "border-rule bg-white"
                      )}
                    >
                      <div className="flex items-baseline gap-2">
                        <span
                          className={cn(
                            "font-mono text-[0.625rem]",
                            f.severity === "blocking" ? "text-stamp" : "text-ink-faint"
                          )}
                        >
                          {f.severity}
                        </span>
                        {f.field && (
                          <span className="font-mono text-[0.6875rem] text-ink-soft">
                            {f.field}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-[0.875rem] leading-snug">{f.message}</p>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <div className="mt-7">
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
