import { useState } from "react"
import { DOC_MARKS, GROUP_MARKS } from "@/components/Marks"
import type { EvalCase, PacketDocument } from "@/types"
import { cn } from "@/lib/utils"

const GROUPS: { label: string; docs: string[] }[] = [
  { label: "what the carrier already holds", docs: ["records_on_file"] },
  { label: "correspondence", docs: ["broker_email"] },
  {
    label: "the application",
    docs: ["application", "property_section", "liability_section"],
  },
  { label: "schedules", docs: ["sov"] },
  { label: "claims history", docs: ["loss_run_a", "loss_run_b", "no_losses_letter"] },
]

const DESCRIPTIONS: Record<string, string> = {
  records_on_file: "submissions already received for this risk",
  broker_email: "the broker's covering note and the thread behind it",
  application: "who the applicant is, and the declared loss history",
  property_section: "per building: values, construction, protection",
  liability_section: "limits and the schedule of hazards",
  sov: "every location and what it is worth",
  loss_run_a: "the expiring property carrier's claims record",
  loss_run_b: "the expiring liability carrier's claims record",
  no_losses_letter: "written confirmation of a nil claims history",
}

export function PacketBrowser({ evalCase }: { evalCase: EvalCase }) {
  const [open, setOpen] = useState(evalCase.documents[1]?.name ?? evalCase.documents[0].name)
  const current = evalCase.documents.find((d) => d.name === open) ?? evalCase.documents[0]
  const present = new Map(evalCase.documents.map((d) => [d.name, d]))

  return (
    <div className="flex min-h-0 flex-1">
      <nav
        aria-label="packet files"
        className="w-[17rem] shrink-0 overflow-y-auto border-r border-rule-soft px-3 py-3"
      >
        {GROUPS.map((group) => {
          const docs = group.docs
            .map((name) => present.get(name))
            .filter((d): d is PacketDocument => Boolean(d))
          if (docs.length === 0) return null
          return (
            <div key={group.label} className="mb-4">
              <div className="flex items-center gap-1.5 px-2 pb-1">
                {(() => {
                  const Mark = GROUP_MARKS[group.label]
                  return Mark ? <Mark className="h-4 w-5 text-rule" /> : null
                })()}
                <span className="field-label">{group.label}</span>
              </div>
              <ul>
                {docs.map((doc) => {
                  const active = doc.name === open
                  return (
                    <li key={doc.name}>
                      <button
                        type="button"
                        onClick={() => setOpen(doc.name)}
                        className={cn(
                          "pressable w-full rounded-field px-2 py-1.5 text-left transition-colors",
                          active ? "bg-carbon-wash" : "hover:bg-paper-sunk"
                        )}
                      >
                        <span
                          className={cn(
                            "block font-mono text-[0.75rem]",
                            active ? "font-medium text-carbon" : "text-ink"
                          )}
                        >
                          {doc.filename}
                        </span>
                        <span className="mt-0.5 block text-[0.6875rem] leading-snug text-ink-faint">
                          {DESCRIPTIONS[doc.name]}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
          )
        })}
        <p className="px-2 pt-1 text-[0.6875rem] leading-relaxed text-ink-faint">
          {evalCase.documents.length} documents, written by three parties at three
          different times.
        </p>
      </nav>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-rule-soft px-5 py-2">
          <span className="flex items-center gap-2">
            {(() => {
              const Mark = DOC_MARKS[current.name]
              return Mark ? <Mark className="h-4 w-5 text-rule" /> : null
            })()}
            <span className="font-mono text-[0.75rem]">{current.filename}</span>
          </span>
          <span className="font-mono text-micro text-ink-faint">
            {current.body.split("\n").length} lines
          </span>
        </div>
        <div className="min-h-0 flex-1 overflow-auto bg-white">
          <pre className="paper-doc p-5 text-[0.6875rem] leading-[1.65]">{current.body}</pre>
        </div>
      </div>
    </div>
  )
}
