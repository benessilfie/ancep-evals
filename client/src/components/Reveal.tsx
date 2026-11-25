import { useState } from "react"
import type { Answer, Trial } from "@/types"
import { cn } from "@/lib/utils"

interface Props {
  trial: Trial
  field: string
}

function answerOf(trial: Trial, field: string): Answer | null {
  const value = trial.record?.[field]
  return value && typeof value === "object" ? (value as Answer) : null
}

export function Reveal({ trial, field }: Props) {
  const [open, setOpen] = useState(false)
  const answer = answerOf(trial, field)
  const note = trial.notes[0]
  const verdict = trial.fields.find((f) => f.field === field)

  return (
    <section className="mx-auto w-full max-w-[52rem] px-5">
      <p className="text-sm leading-relaxed text-ink-soft">
        Packet 05. The application declares no losses in five years. Two carrier loss runs
        attached to the same packet show two claims. Here is what {trial.modelLabel} wrote
        about it.
      </p>

      <figure className="mt-6">
        <figcaption className="field-label">in its own notes</figcaption>
        <blockquote className="field-box mt-1.5 px-5 py-4 text-[0.9375rem] leading-relaxed">
          {note}
        </blockquote>
      </figure>

      <p className="mt-6 text-sm leading-relaxed text-ink-soft">
        It saw the contradiction and wrote it down. Now look at the field it actually
        handed to the broker&rsquo;s system.
      </p>

      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="group mt-5 inline-flex items-center gap-2.5 rounded-control border border-carbon bg-carbon px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#33407c]"
        >
          Open the record
          <span
            aria-hidden
            className="inline-block h-px w-5 bg-white/60 transition-all group-hover:w-7"
          />
        </button>
      )}

      {open && (
        <div className="mt-5 animate-in fade-in slide-in-from-top-2 duration-500">
          <div className="field-label">the record it produced</div>
          <div className="field-box mt-1.5 overflow-hidden">
            <div className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-0 px-5 py-4 font-mono text-[0.8125rem]">
              <Row label="field" value={field} />
              <Row label="value" value={answer?.value ?? "—"} strong />
              <Row label="mode" value={answer?.mode ?? "—"} />
              <Row
                label="source"
                value={answer?.sources?.[0]?.document ?? "—"}
              />
              <Row
                label="flagged"
                value={answer?.status === "flagged" ? "yes" : "no"}
                strong={answer?.status !== "flagged"}
              />
            </div>

            <div className="border-t border-rule-soft bg-stamp-wash px-5 py-4">
              <p className="text-[0.9375rem] leading-relaxed text-stamp">
                The number is right and the citation is honest. Nothing in this record says
                the application contradicts it, so nobody downstream is asked to look.
              </p>
              {verdict && (
                <p className="mt-2 font-mono text-micro text-stamp/80">
                  graded: {verdict.flagDecision.replace(/_/g, " ")}
                </p>
              )}
            </div>
          </div>

          <p className="mt-5 text-sm leading-relaxed text-ink-soft">
            Every model failed this packet on every run.{" "}
            <span className="text-ink">Nine attempts, nine clean-looking records.</span>
          </p>
        </div>
      )}
    </section>
  )
}

function Row({
  label,
  value,
  strong,
}: {
  label: string
  value: string
  strong?: boolean
}) {
  return (
    <>
      <div className="py-1.5 text-ink-faint">{label}</div>
      <div className={cn("py-1.5", strong ? "font-semibold text-ink" : "text-ink-soft")}>
        {value}
      </div>
    </>
  )
}
