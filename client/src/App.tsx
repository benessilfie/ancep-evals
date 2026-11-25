import { useEffect, useState } from "react"
import { LiveDemo } from "@/components/LiveDemo"
import { PacketDetail } from "@/components/PacketDetail"
import { PacketList } from "@/components/PacketList"
import type { EvalData } from "@/types"

const DEFAULT_CASE = "05-application-contradicts-loss-runs"

export default function App() {
  const [data, setData] = useState<EvalData | null>(null)
  const [selected, setSelected] = useState(DEFAULT_CASE)
  const [view, setView] = useState<"live" | "recorded">("live")

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}eval.json`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null))
  }, [])

  if (!data) {
    return (
      <div className="flex h-dvh items-center justify-center">
        <p className="font-mono text-micro text-ink-faint">loading the run</p>
      </div>
    )
  }

  const current = data.cases.find((c) => c.id === selected) ?? data.cases[0]
  const unbeaten = data.cases.filter((c) => c.trials.every((t) => !t.passed)).length

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <header className="shrink-0 border-b border-rule">
        <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-2 px-5 py-3">
          <div className="flex items-baseline gap-4">
            <span className="font-mono text-[0.8125rem]">submission intake evals</span>
            <span className="hidden text-[0.875rem] text-ink-soft sm:inline">
              Graded on the record the model filed, not the summary it wrote.
            </span>
          </div>
          <div className="flex items-center gap-5">
            <div className="flex rounded-control border border-rule bg-white p-0.5">
              {(["live", "recorded"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setView(mode)}
                  className={
                    "pressable rounded-[3px] px-3.5 py-1.5 text-[0.8125rem] transition-colors " +
                    (view === mode
                      ? "bg-ink text-paper"
                      : "text-ink-soft hover:text-ink")
                  }
                >
                  {mode === "live" ? "Live demo" : "Findings"}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-5 font-mono text-micro text-ink-faint">
            <span>
              <span className="text-stamp">{unbeaten}</span>{" "}
              {unbeaten === 1 ? "packet" : "packets"} no model passed
            </span>
            <span>
              {data.totals.passed}/{data.totals.trials} records accepted
            </span>
            <span className="hidden md:inline">effort {data.effort}</span>
          </div>
        </div>
      </header>

      {view === "recorded" ? (
        <div className="flex min-h-0 flex-1">
          <PacketList
            cases={data.cases}
            models={data.models}
            selected={current.id}
            onSelect={setSelected}
          />
          <PacketDetail key={current.id} evalCase={current} />
        </div>
      ) : (
        <LiveDemo data={data} />
      )}
    </div>
  )
}
