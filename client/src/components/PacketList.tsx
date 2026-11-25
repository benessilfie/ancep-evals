import { useMarker } from "@/lib/marker"
import type { EvalCase, ModelSummary } from "@/types"
import { cn } from "@/lib/utils"

interface Props {
  cases: EvalCase[]
  models: ModelSummary[]
  selected: string
  onSelect: (id: string) => void
}

function tally(evalCase: EvalCase, model: string) {
  const trials = evalCase.trials.filter((t) => t.model === model)
  return { passed: trials.filter((t) => t.passed).length, total: trials.length }
}

export function PacketList({ cases, models, selected, onSelect }: Props) {
  const { track, style } = useMarker<HTMLUListElement>(selected)
  return (
    <nav
      aria-label="packets"
      className="hidden w-[22rem] shrink-0 overflow-y-auto border-r border-rule bg-paper-sunk/40 lg:block"
    >
      <div className="sticky top-0 flex items-center gap-2 border-b border-rule-soft bg-paper-sunk/90 px-4 py-2 backdrop-blur">
        <span className="field-label flex-1">packet</span>
        <span className="field-label mr-1">runs passed</span>
        {models.map((m) => (
          <span key={m.id} className="field-label w-12 text-center">
            {m.label.replace(" 5.5", "")}
          </span>
        ))}
      </div>

      <ul ref={track} className="relative">
        <span
          aria-hidden
          style={style}
          className="marker pointer-events-none absolute top-0 left-0 bg-white shadow-[inset_3px_0_0_var(--color-carbon)]"
        />
        {cases.map((evalCase) => {
          const active = evalCase.id === selected
          const none = evalCase.trials.every((t) => !t.passed)
          return (
            <li key={evalCase.id}>
              <button
                type="button"
                onClick={() => onSelect(evalCase.id)}
                aria-current={active ? "true" : undefined}
                data-on={active ? "true" : undefined}
                className={cn(
                  "pressable relative flex w-full items-start gap-2 border-b border-rule-soft px-4 py-3 text-left transition-colors",
                  !active && "hover:bg-white/60"
                )}
              >
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline gap-2">
                    <span className="font-mono text-[0.6875rem] text-ink-faint">
                      {evalCase.id.slice(0, 2)}
                    </span>
                    {evalCase.kind === "control" && (
                      <span className="font-mono text-[0.625rem] text-seal">control</span>
                    )}
                    {none && (
                      <span className="font-mono text-[0.625rem] text-stamp">
                        none passed
                      </span>
                    )}
                  </span>
                  <span
                    className={cn(
                      "mt-0.5 block text-[0.8125rem] leading-snug",
                      active ? "font-medium text-carbon" : "text-ink"
                    )}
                  >
                    {evalCase.short || evalCase.title}
                  </span>
                </span>
                <span className="flex shrink-0 gap-2 pt-0.5">
                  {models.map((m) => {
                    const { passed, total } = tally(evalCase, m.id)
                    return (
                      <span
                        key={m.id}
                        title={`${m.label}: ${passed} of ${total}`}
                        className={cn(
                          "w-12 text-center font-mono text-[0.6875rem] tabular-nums",
                          passed === 0 && "font-semibold text-stamp",
                          passed > 0 && passed < total && "text-stamp/70",
                          passed === total && "text-ink-faint"
                        )}
                      >
                        {passed}/{total}
                      </span>
                    )
                  })}
                </span>
              </button>
            </li>
          )
        })}
      </ul>

      <div className="px-4 py-4">
        <p className="text-[0.75rem] leading-relaxed text-ink-faint">
          Three packets have nothing wrong with them on purpose. Without them an agent that
          flags every field would score full marks.
        </p>
      </div>
    </nav>
  )
}
