import type { EvalCase, ModelSummary } from "@/types"
import { cn } from "@/lib/utils"

interface Props {
  cases: EvalCase[]
  models: ModelSummary[]
  selected: string
  onSelect: (id: string) => void
}

function score(evalCase: EvalCase, model: string) {
  const trials = evalCase.trials.filter((t) => t.model === model)
  return { passed: trials.filter((t) => t.passed).length, total: trials.length }
}

export function Ledger({ cases, models, selected, onSelect }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="greenbar w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-rule">
            <th className="field-label py-2 pr-4 font-normal">packet</th>
            <th className="field-label py-2 pr-4 font-normal">kind</th>
            {models.map((model) => (
              <th
                key={model.id}
                className="field-label w-24 py-2 pr-4 text-right font-normal"
              >
                {model.label.replace(" 5.5", "")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cases.map((evalCase) => {
            const active = evalCase.id === selected
            const number = evalCase.id.slice(0, 2)
            const name = evalCase.id.slice(3).replace(/-/g, " ")
            return (
              <tr
                key={evalCase.id}
                onClick={() => onSelect(evalCase.id)}
                className={cn(
                  "cursor-pointer border-b border-rule-soft transition-colors",
                  active ? "bg-carbon-wash" : "hover:bg-paper-sunk"
                )}
              >
                <td className="py-2.5 pr-4 align-top">
                  <button
                    type="button"
                    className="text-left"
                    onClick={(e) => {
                      e.stopPropagation()
                      onSelect(evalCase.id)
                    }}
                  >
                    <span className="font-mono text-[0.75rem] text-ink-faint">
                      {number}
                    </span>
                    <span
                      className={cn(
                        "ml-2.5 text-[0.9375rem]",
                        active ? "font-medium text-carbon" : "text-ink"
                      )}
                    >
                      {name}
                    </span>
                  </button>
                </td>
                <td className="py-2.5 pr-4 align-top">
                  <span
                    className={cn(
                      "font-mono text-micro",
                      evalCase.kind === "control" ? "text-seal" : "text-ink-faint"
                    )}
                  >
                    {evalCase.kind}
                  </span>
                </td>
                {models.map((model) => {
                  const { passed, total } = score(evalCase, model.id)
                  const none = passed === 0 && total > 0
                  const all = passed === total && total > 0
                  return (
                    <td key={model.id} className="py-2.5 pr-4 text-right align-top">
                      <span
                        className={cn(
                          "font-mono text-[0.8125rem] tabular-nums",
                          none && "font-semibold text-stamp",
                          !none && !all && "text-stamp/70",
                          all && "text-ink-faint"
                        )}
                      >
                        {passed}/{total}
                      </span>
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
        <tfoot>
          <tr>
            <td className="py-2.5 pr-4 text-[0.8125rem] text-ink-soft" colSpan={2}>
              trials passed
            </td>
            {models.map((model) => (
              <td
                key={model.id}
                className="py-2.5 pr-4 text-right font-mono text-[0.8125rem] tabular-nums text-ink"
              >
                {model.passed}/{model.total}
              </td>
            ))}
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
