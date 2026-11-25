import { useState } from "react"
import { Evidence } from "@/components/Evidence"
import { FormMark, LedgerMark, PaperMark, ScheduleMark, SealMark } from "@/components/Marks"
import type { EvalCase, EvalData } from "@/types"
import { cn } from "@/lib/utils"

const usd = (n: number) => `$${n.toLocaleString("en-US")}`

interface StepView {
  title: string
  body: React.ReactNode
  aside: React.ReactNode
}

export function HowItWorks({
  data,
  onGo,
}: {
  data: EvalData
  onGo: (view: "live" | "recorded") => void
}) {
  const [step, setStep] = useState(0)
  const broken = data.cases.find((c) => c.trials.every((t) => !t.passed)) ?? data.cases[4]
  const controls = data.cases.filter((c) => c.kind === "control")
  const steps = buildSteps(data, broken, controls, onGo)
  const current = steps[step]
  const last = step === steps.length - 1

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-[64rem] px-6 py-10">
        <div className="mb-7">
          <h1 className="max-w-[24ch] text-[1.875rem] leading-[1.12] font-semibold tracking-[-0.02em]">
            An eval set to grade AI on commercial insurance submissions
          </h1>
          <p className="mt-2.5 text-[1rem] text-ink-soft">
            Six steps, about two minutes, then you can run one yourself.
          </p>
        </div>

        <nav className="flex flex-wrap items-center gap-x-2 gap-y-2">
          {steps.map((s, i) => (
            <button
              key={s.title}
              type="button"
              onClick={() => setStep(i)}
              className={cn(
                "pressable rounded-field px-2.5 py-1 text-[0.75rem] transition-colors",
                i === step
                  ? "bg-ink text-paper"
                  : i < step
                    ? "text-ink-soft hover:bg-paper-sunk"
                    : "text-ink-faint hover:bg-paper-sunk"
              )}
            >
              <span className="font-mono text-[0.625rem]">{i + 1}</span>
              <span className="ml-1.5">{s.title}</span>
            </button>
          ))}
        </nav>

        <div className="mt-9 grid gap-10 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
          <div>{current.body}</div>
          <div className="min-w-0">{current.aside}</div>
        </div>

        <div className="mt-10 flex items-center gap-3 border-t border-rule-soft pt-5">
          <button
            type="button"
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            className="pressable rounded-control border border-rule px-4 py-2 text-[0.8125rem] disabled:opacity-40"
          >
            Back
          </button>
          {!last ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="pressable rounded-control bg-ink px-5 py-2 text-[0.8125rem] font-medium text-paper transition-colors hover:bg-ink-lift"
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              onClick={() => onGo("live")}
              className="pressable rounded-control bg-ink px-5 py-2 text-[0.8125rem] font-medium text-paper transition-colors hover:bg-ink-lift"
            >
              Open the live demo
            </button>
          )}
          <span className="ml-auto font-mono text-micro text-ink-faint">
            {step + 1} of {steps.length}
          </span>
        </div>
      </div>
    </div>
  )
}

function buildSteps(
  data: EvalData,
  broken: EvalCase,
  controls: EvalCase[],
  onGo: (view: "live" | "recorded") => void
): StepView[] {
  const f = broken.facts
  const sample = data.cases[1]

  return [
    {
      title: "What this is",
      body: (
        <Prose>
          <p>
            A broker sends an insurer a pile of paperwork and somebody has to read all of
            it and type the facts into a system, and that job is going to AI now.
          </p>
          <p>
            An eval set is how you find out whether it can. You write a fixed set of test
            cases, you write down the right answer to each one before any model sees it,
            then you point a model at them and score what comes back.
          </p>
          <p>
            This one is ten fake submissions put to three Claude models, three separate
            runs each, so {data.totals.trials} graded records in total.
          </p>
          <p className="text-ink">
            Each model fills in the same twenty one fields, and those filled in fields are
            what I grade. Not the paragraph it writes about what it did, because a model
            that fills a field in wrong still writes a confident, convincing paragraph.
          </p>
        </Prose>
      ),
      aside: (
        <Panel label="the ten submissions">
          <ul className="divide-y divide-rule-soft">
            {data.cases.map((c) => (
              <li key={c.id} className="flex items-center gap-3 px-4 py-2">
                <span className="font-mono text-[0.625rem] text-ink-faint">
                  {c.id.slice(0, 2)}
                </span>
                <span className="flex-1 truncate text-[0.8125rem]">{c.short}</span>
                <span
                  className={cn(
                    "font-mono text-[0.625rem]",
                    c.kind === "control" ? "text-seal" : "text-ink-faint"
                  )}
                >
                  {c.kind === "control" ? "nothing wrong" : "one thing broken"}
                </span>
              </li>
            ))}
          </ul>
        </Panel>
      ),
    },
    {
      title: "How I know the answers",
      body: (
        <Prose>
          <p>
            Normally you would pay someone who knows insurance to read real files and mark
            them up, which takes days and expertise I do not have.
          </p>
          <p>
            So I did it the other way round. I wrote down what is true first, then a
            program printed the paperwork out of that record, which means the answer key
            came free and a trap is just me breaking one thing on purpose.
          </p>
        </Prose>
      ),
      aside: (
        <div className="space-y-3">
          <Flow
            mark={<PaperMark className="h-9 w-11 text-rule" />}
            head="the truth record"
            body={`A bakery, ${f?.locationCount ?? 6} shops, ${usd(f?.totalInsured ?? 8400000)} of property, ${f?.lossCount ?? 2} claims worth ${usd(f?.totalIncurred ?? 42000)} between them.`}
          />
          <Flow
            mark={<FormMark className="h-9 w-11 text-rule" />}
            head="the paperwork, printed from it"
            body={`${sample.documents.length} documents. The broker's email, the application and its property and liability sections, the schedule of values, loss runs from both prior carriers.`}
          />
          <Flow
            mark={<LedgerMark className="h-9 w-11 text-rule" />}
            head="then one thing breaks"
            body="Tick the no claims box on the signed form and leave the two real claims in the attached loss runs. The truth record still holds the right answer."
            tone="stamp"
          />
        </div>
      ),
    },
    {
      title: "What I check",
      body: (
        <Prose>
          <p>Three things on every field, and the middle one is the whole point.</p>
          <p>
            Every answer has to carry its provenance, so the agent names the document and
            says whether it read the value or worked it out, and I check that claim against
            the document it named.
          </p>
        </Prose>
      ),
      aside: (
        <div className="space-y-3">
          <Flow
            mark={<ScheduleMark className="h-9 w-11 text-rule" />}
            head="is the number right"
            body={`Did it file ${usd(f?.totalInsured ?? 8400000)} for the property, or something else.`}
          />
          <Flow
            mark={<FormMark className="h-9 w-11 text-rule" />}
            head="did it really read that"
            body="If it says it read the total off the application, that total had better be on the application. Usually it is not anywhere, so the agent sums the schedule and calls it reading, and the number is right but nobody checks the arithmetic again."
            tone="stamp"
          />
          <Flow
            mark={<SealMark className="h-9 w-11 text-rule" />}
            head="did it stop and ask"
            body="When two documents disagree, or one is missing, the right answer is a query, not a value. Picking a side quietly is the failure even when it picks correctly."
          />
        </div>
      ),
    },
    {
      title: "Why some have no trap",
      body: (
        <Prose>
          <p>
            A smoke alarm that goes off all day catches every fire and is useless, so if
            every file had a trap an agent that queried everything would score full marks.
          </p>
          <p>
            {controls.length} of the ten are clean, and raising a query on those counts
            against you. One of them genuinely has no claims with the carrier&rsquo;s nil
            letter attached, which looks almost identical to the file where the loss runs
            are simply missing, and those two need opposite answers.
          </p>
        </Prose>
      ),
      aside: (
        <Panel label="the pair that decides it">
          <div className="grid gap-px bg-rule-soft sm:grid-cols-2">
            <div className="bg-white px-4 py-3">
              <div className="field-label">03 nil losses, letter attached</div>
              <p className="mt-1.5 text-[0.875rem] leading-snug">
                Record zero claims and cite the letter.
              </p>
              <p className="mt-1.5 font-mono text-[0.6875rem] text-seal">
                querying this is wrong
              </p>
            </div>
            <div className="bg-white px-4 py-3">
              <div className="field-label">09 loss runs missing</div>
              <p className="mt-1.5 text-[0.875rem] leading-snug">
                Go back to the broker. Absent is not zero.
              </p>
              <p className="mt-1.5 font-mono text-[0.6875rem] text-stamp">
                recording zero is wrong
              </p>
            </div>
          </div>
        </Panel>
      ),
    },
    {
      title: "What broke",
      body: (
        <Prose>
          <p>
            Every model failed this one on every run, {broken.trials.length} attempts
            between them.
          </p>
          <p>
            They all filed the right claim count with an honest citation and no query, and
            none of them mentioned that the signed form said the opposite.
          </p>
          <p className="text-ink">
            One of them wrote the contradiction into its own notes and filed the clean
            number anyway, so reading what it said you would think it caught the problem,
            and reading what it filed the problem is gone.
          </p>
        </Prose>
      ),
      aside: (
        <div className="overflow-hidden rounded-field border border-rule">
          <Evidence evalCase={broken} />
        </div>
      ),
    },
    {
      title: "Go and try it",
      body: (
        <Prose>
          <p>
            The live demo runs a packet against a model right now and fills the record in
            front of you, so you can watch it miss the thing it was told to watch for.
          </p>
          <p>
            Findings has all {data.totals.trials} runs that already happened, every packet,
            every model, and the field that went wrong in each one.
          </p>
        </Prose>
      ),
      aside: (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card
            mark={<ScheduleMark className="h-7 w-8 text-rule" />}
            head="Live demo"
            body="Read any packet document by document, then run it. About forty seconds."
            hint={`open ${broken.short} first`}
            onClick={() => onGo("live")}
          />
          <Card
            mark={<LedgerMark className="h-7 w-8 text-rule" />}
            head="Findings"
            body={`All ${data.totals.trials} recorded runs, with the record each one filed.`}
            hint="red numbers in the left list are failures"
            onClick={() => onGo("recorded")}
          />
        </div>
      ),
    },
  ]
}

function Prose({ children }: { children: React.ReactNode }) {
  return (
    <div className="space-y-4 text-[1rem] leading-relaxed text-ink-soft">{children}</div>
  )
}

function Panel({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-field border border-rule bg-white">
      <div className="field-label border-b border-rule-soft bg-paper-sunk/60 px-4 py-2">
        {label}
      </div>
      {children}
    </div>
  )
}

function Flow({
  mark,
  head,
  body,
  tone,
}: {
  mark: React.ReactNode
  head: string
  body: string
  tone?: "stamp"
}) {
  return (
    <div
      className={cn(
        "flex items-start gap-4 rounded-field border bg-white px-4 py-3.5",
        tone === "stamp" ? "border-stamp/40" : "border-rule"
      )}
    >
      <span className="mt-0.5 shrink-0">{mark}</span>
      <div>
        <div
          className={cn(
            "text-[0.9375rem] font-medium",
            tone === "stamp" ? "text-stamp" : "text-ink"
          )}
        >
          {head}
        </div>
        <p className="mt-1 text-[0.875rem] leading-relaxed text-ink-soft">{body}</p>
      </div>
    </div>
  )
}

function Card({
  mark,
  head,
  body,
  hint,
  onClick,
}: {
  mark: React.ReactNode
  head: string
  body: string
  hint: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="pressable rounded-control border border-rule bg-white px-5 py-4 text-left transition-colors hover:border-ink-faint"
    >
      <div className="flex items-center gap-2.5">
        {mark}
        <span className="text-[0.9375rem] font-medium">{head}</span>
      </div>
      <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-soft">{body}</p>
      <p className="mt-2.5 font-mono text-[0.6875rem] text-carbon">{hint}</p>
    </button>
  )
}
