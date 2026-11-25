import { useState } from "react"
import { Evidence } from "@/components/Evidence"
import { RecordTable, humanise } from "@/components/RecordTable"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { EvalCase, Trial } from "@/types"
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

  return (
    <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
      <div className="shrink-0 border-b border-rule-soft px-6 py-4">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="text-[1.0625rem] leading-snug font-semibold tracking-[-0.01em]">
            {evalCase.short || evalCase.title}
          </h1>
          <span className="font-mono text-micro text-ink-faint">{evalCase.id}</span>
        </div>
        <p className="mt-1 max-w-[70ch] text-[0.8125rem] leading-snug text-ink-soft">
          {evalCase.title}
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2">
          <span className="field-label">3 runs per model, they are not deterministic</span>
          {MODELS.map((label) => {
            const runs = evalCase.trials.filter((t) => t.modelLabel.startsWith(label))
            if (runs.length === 0) return null
            return (
              <span key={label} className="flex items-center gap-1.5">
                <span className="text-[0.75rem] text-ink-soft">{label}</span>
                {runs.map((t) => (
                  <button
                    key={`${t.model}-${t.rep}`}
                    type="button"
                    onClick={() => setTrial(t)}
                    title={`${t.modelLabel} run ${t.rep + 1} of ${runs.length}`}
                    className={cn(
                      "rounded-field border px-2 py-1 font-mono text-[0.6875rem] transition-colors",
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

      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 flex-1 flex-col overflow-hidden border-r border-rule-soft">
          <Evidence evalCase={evalCase} />

          <Tabs
            defaultValue="__record"
            className="flex min-h-0 flex-1 flex-col gap-0"
          >
            <TabsList className="h-auto shrink-0 flex-wrap justify-start gap-0.5 rounded-none border-b border-rule bg-transparent px-5 pt-2 pb-0">
              <span className="field-label self-center pr-2">output</span>
              <TabsTrigger
                value="__record"
                className="rounded-none px-2 py-1.5 text-[0.75rem] font-medium text-ink [border-width:0_0_2px_0] [border-bottom-color:transparent] [border-style:solid] data-[state=active]:[border-bottom-color:var(--color-carbon)] data-[state=active]:text-carbon"
              >
                the record it filed
              </TabsTrigger>
              <span aria-hidden className="mx-3 self-center text-rule">
                |
              </span>
              <span className="field-label self-center pr-2">
                the {evalCase.documents.length} documents it was given
              </span>
              {evalCase.documents.map((doc) => (
                <TabsTrigger
                  key={doc.name}
                  value={doc.name}
                  className="rounded-none px-2 py-1.5 text-[0.75rem] text-ink-soft [border-width:0_0_2px_0] [border-bottom-color:transparent] [border-style:solid] data-[state=active]:[border-bottom-color:var(--color-carbon)] data-[state=active]:text-carbon"
                >
                  {DOC_NAMES[doc.name] ?? doc.name}
                </TabsTrigger>
              ))}
            </TabsList>
            <TabsContent
              value="__record"
              className="min-h-0 flex-1 overflow-auto bg-white"
            >
              <RecordTable trial={trial} />
            </TabsContent>
            {evalCase.documents.map((doc) => (
              <TabsContent
                key={doc.name}
                value={doc.name}
                className="min-h-0 flex-1 overflow-auto bg-white"
              >
                <pre className="paper-doc p-5 text-[0.6875rem] leading-[1.65]">
                  {doc.body}
                </pre>
              </TabsContent>
            ))}
          </Tabs>
        </section>

        <aside className="w-[21rem] shrink-0 overflow-y-auto px-5 py-4">
          <TrialPanel trial={trial} />

          {evalCase.expectations.length > 0 && (
            <div className="mt-7">
              <div className="field-label">what a correct record does</div>
              <ul className="mt-2.5 space-y-3">
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
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

function TrialPanel({ trial }: { trial: Trial }) {
  const problems = trial.fields.filter(
    (f) =>
      f.valueCorrect === false ||
      f.provenanceOk === false ||
      (f.flagDecision !== "correctly_flagged" && f.flagDecision !== "correctly_not_flagged")
  )

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[0.875rem] font-medium">
          {trial.modelLabel} run {trial.rep + 1}
        </span>
        <span
          className={cn(
            "font-mono text-[0.6875rem]",
            trial.passed ? "text-seal" : "font-semibold text-stamp"
          )}
        >
          {trial.passed ? "accepted" : "rejected"}
        </span>
      </div>

      <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 font-mono text-[0.6875rem]">
        <dt className="text-ink-faint">values right</dt>
        <dd className="tabular-nums">{Math.round(trial.valueScore * 100)}%</dd>
        <dt className="text-ink-faint">citations checked out</dt>
        <dd className="tabular-nums">{Math.round(trial.provenanceScore * 100)}%</dd>
        <dt className="text-ink-faint">conflicts it should have raised</dt>
        <dd className="tabular-nums">{trial.missedFlags}</dd>
        <dt className="text-ink-faint">fields it needlessly queried</dt>
        <dd className="tabular-nums">{trial.spuriousFlags}</dd>
      </dl>

      {problems.length === 0 ? (
        <p className="mt-4 text-[0.75rem] leading-relaxed text-ink-soft">
          Every field correct, and every citation checked against the document it names.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {problems.map((p) => (
            <li key={p.field} className="border-l-2 border-stamp bg-stamp-wash px-3 py-2">
              <div className="font-mono text-[0.6875rem] text-stamp">{p.field}</div>
              <p className="mt-0.5 text-[0.75rem] leading-snug text-ink-soft">
                {humanise(p.detail)}
              </p>
            </li>
          ))}
        </ul>
      )}

      {trial.notes.length > 0 && (
        <details className="mt-4">
          <summary className="field-label cursor-pointer list-none hover:text-ink-soft">
            its own notes ({trial.notes.length})
          </summary>
          <ul className="mt-2 space-y-2">
            {trial.notes.map((note, i) => (
              <li
                key={i}
                className="border-l-2 border-rule pl-3 text-[0.75rem] leading-relaxed text-ink-soft"
              >
                {note}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
