import { useState } from "react"
import { Evidence } from "@/components/Evidence"
import { RecordTable, humanise } from "@/components/RecordTable"
import { Tabs, TabsContent } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { EvalCase, FieldVerdict, Trial } from "@/types"
import { cn } from "@/lib/utils"

const DOC_NAMES: Record<string, string> = {
  records_on_file: "on file",
  broker_email: "email",
  application: "application",
  property_section: "property",
  liability_section: "liability",
  sov: "schedule",
  loss_run_a: "loss run A",
  loss_run_b: "loss run B",
  no_losses_letter: "nil letters",
}

const MODELS = ["Opus", "Sonnet", "Haiku"]

export function PacketDetail({ evalCase }: { evalCase: EvalCase }) {
  const [trial, setTrial] = useState<Trial>(
    evalCase.trials.find((t) => !t.passed) ?? evalCase.trials[0]
  )
  const [tab, setTab] = useState("__record")

  return (
    <main className="flex min-w-0 flex-1 flex-col gap-3 lg:gap-0 lg:overflow-hidden">
      <div className="shrink-0 rounded-field border border-rule bg-paper px-4 py-4 lg:rounded-none lg:border-0 lg:border-b lg:border-rule-soft lg:px-6">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="text-[1.0625rem] leading-snug font-semibold tracking-[-0.01em]">
            {evalCase.short || evalCase.title}
          </h1>
          <span className="font-mono text-micro text-ink-faint">{evalCase.id}</span>
        </div>
        <p className="mt-1 max-w-[70ch] text-[0.8125rem] leading-snug text-ink-soft">
          {evalCase.title}
        </p>

        <div className="mt-3">
          <span className="field-label">3 runs per model, they are not deterministic</span>
          <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2">
          {MODELS.map((label) => {
            const runs = evalCase.trials.filter((t) => t.modelLabel.startsWith(label))
            if (runs.length === 0) return null
            return (
              <span key={label} className="flex items-center gap-1.5">
                <span className="w-[3.25rem] shrink-0 text-[0.75rem] text-ink-soft">{label}</span>
                {runs.map((t) => (
                  <button
                    key={`${t.model}-${t.rep}`}
                    type="button"
                    onClick={() => setTrial(t)}
                    title={`${t.modelLabel} run ${t.rep + 1} of ${runs.length}`}
                    className={cn(
                      "pressable rounded-field border px-2 py-1 font-mono text-[0.6875rem] transition-colors",
                      t === trial
                        ? "border-ink bg-ink text-paper"
                        : t.passed
                          ? "border-rule-soft bg-white text-ink-faint hover:border-rule"
                          : "border-stamp/40 bg-stamp-wash font-semibold text-stamp hover:border-stamp"
                    )}
                  >
                    run {t.rep + 1}
                  </button>
                ))}
              </span>
            )
          })}
          </div>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-3 lg:flex-row lg:gap-0">
        <section className="flex min-w-0 flex-1 flex-col rounded-field border border-rule bg-paper lg:rounded-none lg:border-0 lg:border-r lg:border-rule-soft lg:overflow-hidden">
          <Evidence evalCase={evalCase} />

          <Tabs
            value={tab}
            onValueChange={setTab}
            className="flex min-h-0 flex-1 flex-col gap-0"
          >
            <div className="shrink-0 border-b border-rule px-4 py-3 lg:hidden">
              <Select value={tab} onValueChange={setTab}>
                <SelectTrigger className="pressable w-full rounded-field border border-rule bg-white px-2.5 py-2 text-left text-[0.8125rem]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent
                  position="popper"
                  sideOffset={4}
                  className="pop z-50 max-h-[20rem] w-[var(--radix-select-trigger-width)] overflow-y-auto rounded-field border border-rule bg-white p-1 shadow-[0_10px_30px_-14px_rgba(22,23,26,0.4)]"
                >
                  <SelectItem
                    value="__record"
                    className="cursor-pointer rounded-field px-2.5 py-2 text-[0.8125rem] outline-none focus:bg-paper-sunk data-[state=checked]:bg-carbon-wash data-[state=checked]:font-medium data-[state=checked]:text-carbon"
                  >
                    the record it filed
                  </SelectItem>
                  {evalCase.documents.map((doc) => (
                    <SelectItem
                      key={doc.name}
                      value={doc.name}
                      className="cursor-pointer rounded-field px-2.5 py-2 text-[0.8125rem] outline-none focus:bg-paper-sunk data-[state=checked]:bg-carbon-wash data-[state=checked]:font-medium data-[state=checked]:text-carbon"
                    >
                      {DOC_NAMES[doc.name] ?? doc.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="hidden w-full shrink-0 items-center gap-x-0.5 border-b border-rule px-5 py-2 lg:flex">
              <DocTab active={tab === "__record"} onClick={() => setTab("__record")} strong>
                output
              </DocTab>
              <Select
                value={tab === "__record" ? undefined : tab}
                onValueChange={setTab}
              >
                <SelectTrigger
                  className={cn(
                    "pressable ml-auto w-[14rem] rounded-field border border-rule bg-transparent px-2.5 py-1.5 text-left text-[0.75rem] outline-none focus-visible:border-carbon focus-visible:ring-0",
                    tab !== "__record" ? "border-carbon/40 text-carbon" : "text-ink-soft"
                  )}
                >
                  <SelectValue placeholder="choose a document" />
                </SelectTrigger>
                <SelectContent
                  position="popper"
                  sideOffset={4}
                  className="pop z-50 max-h-[22rem] w-[var(--radix-select-trigger-width)] overflow-y-auto rounded-field border border-rule bg-white p-1 shadow-[0_10px_30px_-14px_rgba(22,23,26,0.4)]"
                >
                  {evalCase.documents.map((doc) => (
                    <SelectItem
                      key={doc.name}
                      value={doc.name}
                      className="cursor-pointer rounded-field px-2.5 py-2 text-[0.8125rem] outline-none focus:bg-paper-sunk data-[state=checked]:bg-carbon-wash data-[state=checked]:font-medium data-[state=checked]:text-carbon"
                    >
                      {DOC_NAMES[doc.name] ?? doc.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <TabsContent
              value="__record"
              className="min-h-0 flex-1 overflow-x-auto bg-white lg:overflow-auto"
            >
              <RecordTable trial={trial} />
            </TabsContent>
            {evalCase.documents.map((doc) => (
              <TabsContent
                key={doc.name}
                value={doc.name}
                className="min-h-0 flex-1 overflow-x-auto bg-white lg:overflow-auto"
              >
                <pre className="paper-doc p-5 text-[0.6875rem] leading-[1.65]">
                  {doc.body}
                </pre>
              </TabsContent>
            ))}
          </Tabs>
        </section>

        <aside className="order-first w-full shrink-0 rounded-field border border-rule bg-paper px-5 py-4 lg:order-none lg:w-[26rem] lg:rounded-none lg:border-0 lg:overflow-y-auto">
          <TrialPanel trial={trial} />

          {trial.notes.length > 0 && (
            <Fold
              className="mt-6"
              summary={`what the model said about this packet (${trial.notes.length})`}
            >
              <ul className="space-y-2">
                {trial.notes.map((note, i) => (
                  <li
                    key={i}
                    className="border-l-2 border-rule pl-3 text-[0.8125rem] leading-relaxed text-ink-soft"
                  >
                    {note}
                  </li>
                ))}
              </ul>
            </Fold>
          )}

          {evalCase.expectations.length > 0 && (
            <Fold className="mt-3" summary="what a correct record does">
              <ul className="space-y-3">
                {evalCase.expectations.map((e) => (
                  <li key={e.field} className="border-l-2 border-rule pl-3">
                    <div className="font-mono text-[0.6875rem]">
                      {e.field}{" "}
                      <span
                        className={e.outcome === "flagged" ? "text-stamp" : "text-seal"}
                      >
                        {e.outcome}
                      </span>
                    </div>
                    <p className="mt-1 text-[0.75rem] leading-relaxed text-ink-soft">
                      {e.rationale}
                    </p>
                    <a
                      href={e.source}
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-[0.625rem] text-carbon underline-offset-2 hover:underline"
                    >
                      source
                    </a>
                  </li>
                ))}
              </ul>
            </Fold>
          )}
        </aside>
      </div>
    </main>
  )
}

function Fold({
  summary,
  children,
  className,
}: {
  summary: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <details className={cn("fold group border-t border-rule-soft pt-3", className)}>
      <summary className="pressable flex cursor-pointer list-none items-center gap-1.5 rounded-field text-[0.8125rem] text-ink-soft outline-none hover:text-ink focus-visible:text-carbon focus-visible:underline focus-visible:decoration-carbon/40 focus-visible:underline-offset-4">
        <span
          aria-hidden
          className="font-mono text-[0.625rem] transition-transform group-open:rotate-90"
        >
          &gt;
        </span>
        {summary}
      </summary>
      <div className="mt-3">{children}</div>
    </details>
  )
}

function DocTab({
  active,
  strong,
  onClick,
  children,
}: {
  active: boolean
  strong?: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "true" : undefined}
      className={cn(
        "pressable shrink-0 px-2 py-1.5 text-[0.75rem] [border-style:solid] [border-width:0_0_2px_0] transition-colors",
        strong && "font-medium",
        active
          ? "[border-bottom-color:var(--color-carbon)] text-carbon"
          : "[border-bottom-color:transparent] text-ink-soft hover:text-ink"
      )}
    >
      {children}
    </button>
  )
}

function fieldLabel(field: string): string {
  return field.replace(/_/g, " ").replace(/\busd\b/, "").replace(/\b5y\b/, "in 5 years").trim()
}

function whyItFailed(f: FieldVerdict): string {
  if (f.flagDecision === "missed_flag") {
    return "It filed a value here. This field should have gone back to a human instead."
  }
  if (f.flagDecision === "spurious_flag") {
    return "It sent this back to a human. The documents answer it, so nothing needed raising."
  }
  if (f.valueCorrect === false) return humanise(f.detail)
  if (f.provenanceOk === false) {
    return f.provenanceDetail ? humanise(f.provenanceDetail) : humanise(f.detail)
  }
  return humanise(f.detail)
}

function TrialPanel({ trial }: { trial: Trial }) {
  const problems = trial.fields.filter(
    (f) =>
      f.valueCorrect === false ||
      f.provenanceOk === false ||
      (f.flagDecision !== "correctly_flagged" && f.flagDecision !== "correctly_not_flagged")
  )

  const scores: { value: string; label: string; bad: boolean }[] = [
    {
      value: `${Math.round(trial.valueScore * 100)}%`,
      label: "values right",
      bad: trial.valueScore < 1,
    },
    {
      value: `${Math.round(trial.provenanceScore * 100)}%`,
      label: "citations held up",
      bad: trial.provenanceScore < 1,
    },
    {
      value: String(trial.missedFlags),
      label: trial.missedFlags === 1 ? "conflict missed" : "conflicts missed",
      bad: trial.missedFlags > 0,
    },
    {
      value: String(trial.spuriousFlags),
      label: "queried needlessly",
      bad: trial.spuriousFlags > 0,
    },
  ]

  return (
    <div>
      <div
        className={cn(
          "rounded-field border px-4 py-3.5",
          trial.passed ? "border-seal/35 bg-seal-wash/40" : "border-stamp/40 bg-stamp-wash/50"
        )}
      >
        <div
          className={cn(
            "field-label",
            trial.passed ? "text-seal/70" : "text-stamp/70"
          )}
        >
          eval result
        </div>
        <div
          className={cn(
            "mt-1 text-[1.375rem] leading-none font-semibold tracking-[-0.01em]",
            trial.passed ? "text-seal" : "text-stamp"
          )}
        >
          {trial.passed ? "Passed" : "Failed"}
        </div>
        <div className="mt-1.5 text-[0.8125rem] text-ink-soft">
          {trial.modelLabel} · run {trial.rep + 1} of 3
        </div>
      </div>

      {problems.length === 0 ? (
        <p className="mt-4 text-[0.8125rem] leading-relaxed text-ink-soft">
          Every graded field matched, and every citation pointed at a document that really
          contains the value.
        </p>
      ) : (
        <ul className="mt-4 space-y-2.5">
          {problems.map((p) => (
            <li key={p.field} className="border-l-2 border-stamp pl-3">
              <div className="text-[0.8125rem] font-medium">{fieldLabel(p.field)}</div>
              <p className="mt-0.5 text-[0.8125rem] leading-snug text-ink-soft">
                {whyItFailed(p)}
              </p>
            </li>
          ))}
        </ul>
      )}

      <dl className="mt-5 grid grid-cols-2 gap-px border-t border-rule-soft bg-rule-soft">
        {scores.map((s) => (
          <div key={s.label} className="bg-paper px-3 py-2.5">
            <dd
              className={cn(
                "font-mono text-[1rem] tabular-nums",
                s.bad ? "text-stamp" : "text-ink"
              )}
            >
              {s.value}
            </dd>
            <dt className="mt-0.5 text-[0.6875rem] leading-tight text-ink-faint">
              {s.label}
            </dt>
          </div>
        ))}
      </dl>
    </div>
  )
}
