import { useEffect, useState } from "react"
import { HowItWorks } from "@/components/HowItWorks"
import { LiveDemo } from "@/components/LiveDemo"
import { PacketDetail } from "@/components/PacketDetail"
import { PacketList } from "@/components/PacketList"
import { PacketPicker } from "@/components/PacketPicker"
import type { EvalData } from "@/types"

const DEFAULT_CASE = "05-application-contradicts-loss-runs"

export default function App() {
  const [data, setData] = useState<EvalData | null>(null)
  const [selected, setSelected] = useState(DEFAULT_CASE)
  const [view, setView] = useState<"start" | "live" | "recorded">("start")

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
        <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-2.5 px-4 py-2.5 sm:px-5 sm:py-3">
          <div className="flex items-baseline gap-3">
            <span className="text-[0.875rem] leading-snug font-medium">
              <span className="sm:hidden">An eval set for insurance submissions</span>
              <span className="hidden sm:inline">
                An eval set to grade AI on commercial insurance submissions
              </span>
            </span>
            <span className="hidden text-[0.8125rem] text-ink-soft lg:inline">
              graded on what the model filed, not what it said it did
            </span>
          </div>
          <div className="flex w-full items-center gap-5 sm:w-auto">
            <div className="flex w-full rounded-control border border-rule bg-white p-0.5 sm:w-auto">
              {(["start", "live", "recorded"] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setView(mode)}
                  className={
                    "pressable flex-1 rounded-[3px] px-3.5 py-1.5 text-[0.8125rem] transition-colors sm:flex-none " +
                    (view === mode
                      ? "bg-ink text-paper"
                      : "text-ink-soft hover:text-ink")
                  }
                >
                  {mode === "start" ? "Start here" : mode === "live" ? "Live demo" : "Findings"}
                </button>
              ))}
            </div>
          </div>
          <div className="hidden items-center gap-5 font-mono text-micro text-ink-faint md:flex">
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

      {view === "start" ? (
        <HowItWorks data={data} onGo={setView} />
      ) : view === "recorded" ? (
        <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto bg-paper-sunk/70 p-3 lg:flex-row lg:gap-0 lg:bg-transparent lg:p-0 lg:overflow-hidden">
          <PacketPicker cases={data.cases} selected={current.id} onSelect={setSelected} />
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
