import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { EvalCase, Trial } from "@/types"
import { cn } from "@/lib/utils"

const DOCUMENT_LABELS: Record<string, string> = {
  records_on_file: "records on file",
  broker_email: "broker email",
  application: "application",
  property_section: "property",
  liability_section: "liability",
  sov: "schedule of values",
  loss_run_a: "loss run A",
  loss_run_b: "loss run B",
  no_losses_letter: "no losses letters",
}

export function CaseSheet({ evalCase }: { evalCase: EvalCase }) {
  const [trial, setTrial] = useState<Trial | null>(null)
  const active = trial ?? evalCase.trials[0]

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="min-w-0">
        <h3 className="text-[1.375rem] leading-snug font-semibold tracking-[-0.01em]">
          {evalCase.title}
        </h3>
        <p className="mt-1.5 font-mono text-micro text-ink-faint">
          {evalCase.id}
          {evalCase.corruption ? ` · ${evalCase.corruption.replace(/_/g, " ")}` : ""}
        </p>

        <Tabs defaultValue={evalCase.documents[1]?.name ?? evalCase.documents[0].name}>
          <TabsList className="mt-6 h-auto flex-wrap justify-start gap-1 rounded-none border-b border-rule bg-transparent p-0">
            {evalCase.documents.map((doc) => (
              <TabsTrigger
                key={doc.name}
                value={doc.name}
                className="rounded-none border-0 border-b-2 border-transparent bg-transparent px-2.5 py-2 text-[0.8125rem] text-ink-soft shadow-none data-[state=active]:border-carbon data-[state=active]:bg-transparent data-[state=active]:text-carbon data-[state=active]:shadow-none"
              >
                {DOCUMENT_LABELS[doc.name] ?? doc.name}
              </TabsTrigger>
            ))}
          </TabsList>
          {evalCase.documents.map((doc) => (
            <TabsContent key={doc.name} value={doc.name} className="mt-0">
              <div className="overflow-x-auto border-x border-b border-rule-soft bg-white">
                <pre className="paper-doc p-5">{doc.body}</pre>
              </div>
              <p className="mt-2 font-mono text-micro text-ink-faint">{doc.filename}</p>
            </TabsContent>
          ))}
        </Tabs>
      </div>

      <aside className="min-w-0 space-y-7">
        {evalCase.expectations.length > 0 && (
          <div>
            <div className="field-label">what a correct record does</div>
            <ul className="mt-2 space-y-3.5">
              {evalCase.expectations.map((e) => (
                <li key={e.field} className="border-l-2 border-rule pl-3.5">
                  <div className="font-mono text-[0.75rem] text-ink">
                    {e.field}{" "}
                    <span
                      className={cn(
                        e.outcome === "flagged" ? "text-stamp" : "text-seal"
                      )}
                    >
                      {e.outcome}
                      {e.mode ? ` · ${e.mode}` : ""}
                    </span>
                  </div>
                  <p className="mt-1 text-[0.8125rem] leading-relaxed text-ink-soft">
                    {e.rationale}
                  </p>
                  <a
                    href={e.source}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-block font-mono text-micro text-carbon underline-offset-2 hover:underline"
                  >
                    source
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div>
          <div className="field-label">runs</div>
          <div className="mt-2 space-y-1">
            {evalCase.trials.map((t) => {
              const on = t === active
              return (
                <button
                  key={`${t.model}-${t.rep}`}
                  type="button"
                  onClick={() => setTrial(t)}
                  className={cn(
                    "flex w-full items-center justify-between gap-3 rounded-field px-2.5 py-1.5 text-left text-[0.8125rem] transition-colors",
                    on ? "bg-carbon-wash text-carbon" : "hover:bg-paper-sunk"
                  )}
                >
                  <span>
                    {t.modelLabel}
                    <span className="ml-1.5 font-mono text-micro text-ink-faint">
                      rep {t.rep}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "font-mono text-micro",
                      t.passed ? "text-seal" : "font-semibold text-stamp"
                    )}
                  >
                    {t.passed ? "pass" : "fail"}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {active && <TrialDetail trial={active} />}
      </aside>
    </div>
  )
}

function TrialDetail({ trial }: { trial: Trial }) {
  const problems = trial.fields.filter(
    (f) =>
      f.valueCorrect === false ||
      f.provenanceOk === false ||
      (f.flagDecision !== "correctly_flagged" && f.flagDecision !== "correctly_not_flagged")
  )

  return (
    <div>
      <div className="field-label">
        {trial.modelLabel} rep {trial.rep}
      </div>
      <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-micro">
        <dt className="text-ink-faint">values right</dt>
        <dd className="text-right tabular-nums">
          {Math.round(trial.valueScore * 100)}%
        </dd>
        <dt className="text-ink-faint">citations honest</dt>
        <dd className="text-right tabular-nums">
          {Math.round(trial.provenanceScore * 100)}%
        </dd>
        <dt className="text-ink-faint">missed flags</dt>
        <dd className="text-right tabular-nums">{trial.missedFlags}</dd>
        <dt className="text-ink-faint">needless flags</dt>
        <dd className="text-right tabular-nums">{trial.spuriousFlags}</dd>
      </dl>

      {problems.length > 0 && (
        <ul className="mt-3 space-y-2.5">
          {problems.map((p) => (
            <li key={p.field} className="border-l-2 border-stamp bg-stamp-wash px-3 py-2">
              <div className="font-mono text-[0.75rem] text-stamp">{p.field}</div>
              <p className="mt-0.5 text-[0.8125rem] leading-snug text-ink-soft">
                {p.detail}
              </p>
            </li>
          ))}
        </ul>
      )}

      {trial.notes.length > 0 && (
        <details className="mt-4 group">
          <summary className="field-label cursor-pointer list-none hover:text-ink-soft">
            what it wrote in its notes ({trial.notes.length})
          </summary>
          <ul className="mt-2 space-y-2">
            {trial.notes.map((note, i) => (
              <li
                key={i}
                className="border-l-2 border-rule pl-3 text-[0.8125rem] leading-relaxed text-ink-soft"
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
