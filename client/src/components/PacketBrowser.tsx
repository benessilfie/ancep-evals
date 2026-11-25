import { useState } from "react"
import { DOC_MARKS } from "@/components/Marks"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { EvalCase } from "@/types"
import { cn } from "@/lib/utils"

const ORDER = [
  "records_on_file",
  "broker_email",
  "slip",
  "application",
  "property_section",
  "liability_section",
  "sov",
  "loss_run_a",
  "loss_run_b",
  "no_losses_letter",
  "slip",
]

const NAMES: Record<string, string> = {
  records_on_file: "Already on file",
  broker_email: "Broker email",
  application: "Application",
  property_section: "Property section",
  liability_section: "Liability section",
  sov: "Schedule of values",
  loss_run_a: "Loss run, Meridian",
  loss_run_b: "Loss run, Callaghan",
  no_losses_letter: "Nil claims letters",
  slip: "Market reform slip",
}

const WHAT: Record<string, string> = {
  records_on_file: "What this carrier has already received for this risk.",
  broker_email: "The covering note, and the thread with the client behind it.",
  application: "Who the applicant is, the premises, and the declared loss history.",
  property_section: "Per building: values, coinsurance, construction and protection.",
  liability_section: "Limits, deductibles and the schedule of rated hazards.",
  sov: "Every insured location and what each one is worth.",
  loss_run_a: "The expiring property carrier's claims record, as of a valuation date.",
  loss_run_b: "The expiring liability carrier's claims record, in its own layout.",
  no_losses_letter: "Written confirmation from a carrier that there are no claims.",
  slip: "The London market contract. Risk details, period, sum insured and claims experience.",
}

export function PacketBrowser({ evalCase }: { evalCase: EvalCase }) {
  const ordered = [...evalCase.documents].sort(
    (a, b) => ORDER.indexOf(a.name) - ORDER.indexOf(b.name)
  )
  const [open, setOpen] = useState(
    ordered.find((d) => d.name === "application")?.name ?? ordered[0].name
  )
  const current = ordered.find((d) => d.name === open) ?? ordered[0]
  const position = ordered.findIndex((d) => d.name === current.name) + 1

  return (
    <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
      <div className="shrink-0 border-b border-rule-soft px-4 py-3 lg:hidden">
        <Select value={current.name} onValueChange={setOpen}>
          <SelectTrigger className="pressable w-full rounded-field border border-rule bg-white px-2.5 py-2 text-left text-[0.8125rem]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent
            position="popper"
            sideOffset={4}
            className="pop z-50 max-h-[20rem] w-[var(--radix-select-trigger-width)] overflow-y-auto rounded-field border border-rule bg-white p-1 shadow-[0_10px_30px_-14px_rgba(22,23,26,0.4)]"
          >
            {ordered.map((doc) => {
              const Mark = DOC_MARKS[doc.name]
              return (
                <SelectItem
                  key={doc.name}
                  value={doc.name}
                  className="cursor-pointer rounded-field px-2.5 py-2 text-[0.8125rem] outline-none focus:bg-paper-sunk data-[state=checked]:bg-carbon-wash data-[state=checked]:font-medium data-[state=checked]:text-carbon"
                >
                  <span className="flex w-full items-center gap-2.5">
                    {Mark ? <Mark className="h-4 w-5 shrink-0 text-rule" /> : null}
                    <span className="min-w-0 flex-1 truncate">
                      {NAMES[doc.name] ?? doc.name}
                    </span>
                    <span className="shrink-0 font-mono text-[0.625rem] text-ink-faint">
                      {doc.body.split("\n").length}
                    </span>
                  </span>
                </SelectItem>
              )
            })}
          </SelectContent>
        </Select>
        <p className="mt-1.5 font-mono text-[0.6875rem] text-ink-faint">
          document {position} of {ordered.length}
        </p>
      </div>

      <nav
        aria-label="documents in this packet"
        className="hidden w-[16rem] shrink-0 overflow-y-auto border-r border-rule-soft py-2 lg:block"
      >
        <ul>
          {ordered.map((doc) => {
            const active = doc.name === open
            const Mark = DOC_MARKS[doc.name]
            const lines = doc.body.split("\n").length
            return (
              <li key={doc.name}>
                <button
                  type="button"
                  onClick={() => setOpen(doc.name)}
                  aria-current={active ? "true" : undefined}
                  className={cn(
                    "pressable flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors",
                    active
                      ? "bg-carbon-wash shadow-[inset_2px_0_0_var(--color-carbon)]"
                      : "hover:bg-paper-sunk"
                  )}
                >
                  {Mark ? (
                    <Mark
                      className={cn(
                        "h-5 w-6 shrink-0",
                        active ? "text-carbon/55" : "text-rule"
                      )}
                    />
                  ) : null}
                  <span
                    className={cn(
                      "flex-1 truncate text-[0.8125rem]",
                      active ? "font-medium text-carbon" : "text-ink"
                    )}
                  >
                    {NAMES[doc.name] ?? doc.name}
                  </span>
                  <span className="shrink-0 font-mono text-[0.625rem] tabular-nums text-ink-faint">
                    {lines}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
        <p className="px-3 pt-3 text-[0.6875rem] leading-relaxed text-ink-faint">
          {ordered.length} documents, written by three parties at three different times.
          The number is how many lines long each one is.
        </p>
      </nav>

      <div className="flex min-w-0 flex-1 flex-col lg:overflow-hidden">
        <div className="shrink-0 border-b border-rule-soft px-5 py-3">
          <div className="flex items-baseline justify-between gap-4">
            <h3 className="text-[0.9375rem] font-semibold">
              {NAMES[current.name] ?? current.name}
            </h3>
            <span className="shrink-0 font-mono text-micro text-ink-faint">
              {current.filename}
            </span>
          </div>
          <p className="mt-1 max-w-[70ch] text-[0.8125rem] leading-snug text-ink-soft">
            {WHAT[current.name]}
          </p>
        </div>
        <div className="min-h-0 flex-1 overflow-x-auto bg-white lg:overflow-auto">
          <pre className="paper-doc p-5 text-[0.6875rem] leading-[1.65]">{current.body}</pre>
        </div>
      </div>
    </div>
  )
}
