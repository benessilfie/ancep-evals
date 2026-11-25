import { SealMark } from "@/components/Marks"
import { RECORD_FIELDS } from "@/components/BlankRecord"
import type { Answer, EvalCase } from "@/types"
import { cn } from "@/lib/utils"

export interface Graded {
  passed: boolean
  valueScore: number
  provenanceScore: number
}

interface Finding {
  check: string
  severity: "blocking" | "query" | "note"
  field: string | null
  message: string
}

const TESTS: Record<string, { tests: string; expect: string }> = {
  "01-clean-single-location": {
    tests: "Nothing is wrong with this one.",
    expect: "Fill in all twenty one fields. Raising a query on anything here counts against it.",
  },
  "02-clean-total-stated": {
    tests: "The broker states the total in the email.",
    expect: "Read the total off the email, and say it read it rather than worked it out.",
  },
  "03-clean-no-losses-letter": {
    tests: "There are genuinely no claims, and the carrier's letter confirms it.",
    expect: "Record zero claims and cite the letter. Raising a query here is wrong.",
  },
  "04-stale-thread": {
    tests: "The figure at the top of the email thread was corrected further down it.",
    expect: "Use the corrected figure, not the one that appears first.",
  },
  "05-application-contradicts-loss-runs": {
    tests: "The signed form says no claims. The attached records show two.",
    expect: "Raise a query. Filing either number quietly is the failure, even the right one.",
  },
  "06-derived-total": {
    tests: "No document states a total. It can only be added up.",
    expect: "Sum the schedule, and declare that it derived the figure rather than read it.",
  },
  "07-loss-run-column-mislabel": {
    tests: "On this carrier's layout the paid column does not reconcile.",
    expect: "Raise a query on the paid figure. Paid plus outstanding does not equal incurred.",
  },
  "08-sov-page-break": {
    tests: "One location is split across a page break in the schedule.",
    expect: "Count all six locations and total all six, including the split one.",
  },
  "09-missing-loss-runs": {
    tests: "The loss runs the form points at are not in the packet.",
    expect: "Raise a query on the claims fields. Absent is not the same as zero.",
  },
  "10-duplicate-submission": {
    tests: "This risk was submitted before, and the revenue has changed since.",
    expect: "Mark it as an update of the earlier submission rather than a new risk.",
  },
}

const LABELS = new Map(RECORD_FIELDS.map((f) => [f.field, f.label]))

export function RunVerdict({
  evalCase,
  graded,
  findings,
  answers,
  uploaded,
}: {
  evalCase?: EvalCase
  graded: Graded | null
  findings: Finding[]
  answers: Map<string, Answer>
  uploaded: boolean
}) {
  const raised = [...answers.entries()].filter(([, a]) => a.status === "flagged")
  const blocking = findings.filter((f) => f.severity === "blocking")
  const copy = evalCase ? TESTS[evalCase.id] : undefined

  const headline = uploaded
    ? blocking.length > 0
      ? `${blocking.length} thing${blocking.length === 1 ? "" : "s"} in your documents did not hold up`
      : "Every claim the agent made checks out against your documents"
    : graded?.passed
      ? "It did the right thing here"
      : "It got this one wrong"

  const tone: "seal" | "stamp" = uploaded
    ? blocking.length > 0
      ? "stamp"
      : "seal"
    : graded?.passed
      ? "seal"
      : "stamp"

  return (
    <section
      className={cn(
        "rounded-field border bg-white",
        tone === "seal" ? "border-seal/35" : "border-stamp/45"
      )}
    >
      <div
        className={cn(
          "flex items-start gap-3.5 border-b px-5 py-4",
          tone === "seal" ? "border-seal/20 bg-seal-wash/40" : "border-stamp/20 bg-stamp-wash/50"
        )}
      >
        <SealMark
          className={cn("mt-0.5 h-9 w-11 shrink-0", tone === "seal" ? "text-seal/55" : "text-stamp/50")}
        />
        <div className="min-w-0">
          <h3
            className={cn(
              "text-[1.0625rem] leading-snug font-semibold",
              tone === "seal" ? "text-seal" : "text-stamp"
            )}
          >
            {headline}
          </h3>
          <p className="mt-1 text-[0.875rem] leading-relaxed text-ink-soft">
            {raised.length === 0
              ? `It filled in all ${answers.size} fields and sent nothing back for review.`
              : `It filled in ${answers.size - raised.length} fields and sent ${raised.length} back for a human: ${raised
                  .map(([f]) => LABELS.get(f) ?? f)
                  .join(", ")}.`}
          </p>
        </div>
      </div>

      {copy && (
        <dl className="grid gap-px bg-rule-soft sm:grid-cols-2">
          <div className="bg-white px-5 py-3.5">
            <dt className="field-label">what this packet tests</dt>
            <dd className="mt-1.5 text-[0.875rem] leading-relaxed">{copy.tests}</dd>
          </div>
          <div className="bg-white px-5 py-3.5">
            <dt className="field-label">what should happen</dt>
            <dd className="mt-1.5 text-[0.875rem] leading-relaxed">{copy.expect}</dd>
          </div>
        </dl>
      )}

      {uploaded && (
        <div className="border-t border-rule-soft px-5 py-3.5">
          <div className="field-label">what was checked</div>
          <p className="mt-1.5 max-w-[70ch] text-[0.875rem] leading-relaxed text-ink-soft">
            There is no answer key for your documents, so nothing here compares against one.
            These checks read the record back against the files you supplied: every citation
            has to point at a document that exists, the value has to actually appear where it
            says, and any figure it added up has to reconcile.
          </p>
        </div>
      )}

      {findings.length > 0 && (
        <ul className="divide-y divide-rule-soft border-t border-rule-soft">
          {findings.map((f, i) => (
            <li key={i} className="flex items-start gap-3 px-5 py-3">
              <span
                className={cn(
                  "mt-[0.2rem] shrink-0 font-mono text-[0.625rem]",
                  f.severity === "blocking" ? "text-stamp" : "text-ink-faint"
                )}
              >
                {f.severity === "blocking" ? "stop" : f.severity}
              </span>
              <div className="min-w-0">
                <p className="text-[0.875rem] leading-snug">{f.message}</p>
                {f.field && (
                  <span className="mt-0.5 block font-mono text-[0.6875rem] text-ink-faint">
                    {LABELS.get(f.field) ?? f.field}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
