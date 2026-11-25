import { useEffect, useState } from "react"
import { CaseSheet } from "@/components/CaseSheet"
import { Ledger } from "@/components/Ledger"
import { Reveal } from "@/components/Reveal"
import type { EvalData } from "@/types"

const HERO_CASE = "05-application-contradicts-loss-runs"
const HERO_FIELD = "loss_count_5y"

export default function App() {
  const [data, setData] = useState<EvalData | null>(null)
  const [selected, setSelected] = useState(HERO_CASE)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}eval.json`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null))
  }, [])

  if (!data) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <p className="font-mono text-micro text-ink-faint">loading results</p>
      </div>
    )
  }

  const heroCase = data.cases.find((c) => c.id === HERO_CASE) ?? data.cases[0]
  const heroTrial =
    heroCase.trials.find((t) => t.model.includes("opus") && !t.passed) ?? heroCase.trials[0]
  const current = data.cases.find((c) => c.id === selected) ?? data.cases[0]

  return (
    <div className="min-h-dvh">
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-[76rem] flex-wrap items-baseline justify-between gap-x-8 gap-y-2 px-5 py-3.5">
          <span className="font-mono text-[0.8125rem] text-ink">
            submission intake evals
          </span>
          <span className="font-mono text-micro text-ink-faint">
            {data.totals.trials} trials · {data.models.length} models · {data.reps} runs each
            · effort {data.effort}
          </span>
        </div>
      </header>

      <main>
        <section className="border-b border-rule-soft py-16 sm:py-20">
          <div className="mx-auto w-full max-w-[52rem] px-5">
            <div className="field-label">finding</div>
            <h1 className="field-box mt-1.5 px-5 py-5 text-[1.75rem] leading-[1.25] font-semibold tracking-[-0.015em] sm:text-[2.125rem]">
              The agent saw the contradiction, wrote it down, and signed off the field
              anyway.
            </h1>
          </div>
          <div className="mt-10">
            <Reveal trial={heroTrial} field={HERO_FIELD} />
          </div>
        </section>

        <section className="border-b border-rule-soft py-14">
          <div className="mx-auto w-full max-w-[76rem] px-5">
            <h2 className="text-lg font-semibold tracking-[-0.01em]">
              Ten packets, graded on the record rather than the summary
            </h2>
            <p className="mt-2 max-w-[46rem] text-[0.9375rem] leading-relaxed text-ink-soft">
              Each packet is generated from a truth record, so every right answer is known
              before a model sees it. Three packets have no trick in them, because an agent
              that flags everything would otherwise score full marks.
            </p>
            <div className="mt-7">
              <Ledger
                cases={data.cases}
                models={data.models}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>
        </section>

        <section className="py-14">
          <div className="mx-auto w-full max-w-[76rem] px-5">
            <CaseSheet key={current.id} evalCase={current} />
          </div>
        </section>
      </main>

      <footer className="border-t border-rule">
        <div className="mx-auto max-w-[76rem] px-5 py-6">
          <p className="max-w-[46rem] text-[0.8125rem] leading-relaxed text-ink-soft">
            Every packet here is synthetic. The forms follow industry field names but are
            not ACORD forms, which are licensed. The author does not work in insurance, so
            each expected answer carries a citation you can argue with.
          </p>
        </div>
      </footer>
    </div>
  )
}
