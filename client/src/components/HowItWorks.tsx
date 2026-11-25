import { FormMark, LedgerMark, PaperMark, ScheduleMark, SealMark } from "@/components/Marks"
import type { EvalData } from "@/types"

export function HowItWorks({
  data,
  onGo,
}: {
  data: EvalData
  onGo: (view: "live" | "recorded") => void
}) {
  const unbeaten = data.cases.filter((c) => c.trials.every((t) => !t.passed))
  const controls = data.cases.filter((c) => c.kind === "control").length

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <article className="mx-auto w-full max-w-[50rem] px-6 py-12">
        <h1 className="max-w-[19ch] text-[2.125rem] leading-[1.1] font-semibold tracking-[-0.025em] sm:text-[2.75rem]">
          An AI spotted the problem, wrote it down, and filed a clean report anyway.
        </h1>

        <div className="mt-7 space-y-4 text-[1.0625rem] leading-relaxed text-ink-soft">
          <p>
            When a business wants insurance, its broker sends the insurer a pile of
            paperwork. Someone has to read all of it and type the facts into a system. That
            job is now being handed to AI.
          </p>
          <p>
            So I made ten fake submissions where I already know every right answer, gave
            them to three Claude models, three goes each, and checked{" "}
            <strong className="font-medium text-ink">what they actually typed in</strong> —
            not the confident paragraph they wrote about it.
          </p>
        </div>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          How I know the right answers
        </h2>
        <p className="mt-2 max-w-[62ch] text-[0.9375rem] leading-relaxed text-ink-soft">
          Normally you would pay someone who knows insurance to read real files and mark
          them up. That takes days. I did it backwards instead.
        </p>

        <ol className="mt-7 space-y-7">
          <Step
            mark={<PaperMark className="h-10 w-12 text-rule" />}
            head="First decide what is true"
            body="A bakery with six shops. Property worth $8,400,000 in total. Two claims in the last five years, one for $12,000 and one for $30,000."
          />
          <Step
            mark={<FormMark className="h-10 w-12 text-rule" />}
            head="Then print the paperwork from that"
            body="An email from the broker, the application form the client signed, a spreadsheet listing all six shops, and claims records from the two previous insurers."
            note="Because the facts came first, the paperwork can never disagree with the answer key by accident."
          />
          <Step
            mark={<LedgerMark className="h-10 w-12 text-rule" />}
            head="Then break exactly one thing"
            body="On the signed form, tick the box that says no claims in five years. Leave the two real claims sitting in the attached records."
            note="Now the right answer is not a number. It is: these two documents disagree, go and ask the broker."
          />
        </ol>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          Three things get checked
        </h2>
        <dl className="mt-5 space-y-5">
          <Check
            head="Is the number right?"
            body="Did it say the property is worth $8,400,000, or $7,900,000?"
          />
          <Check
            head="Did it really read that, or work it out?"
            body="If it says &ldquo;I read the total off the form&rdquo;, the total had better be on the form. Often it is not there at all, and the agent added up the spreadsheet and called it reading. Same number, but now nobody double-checks it."
          />
          <Check
            head="Did it stop when it should have?"
            body="When the form says no claims and the records show two, the right answer is to raise it. Picking one and moving on is the failure, even when it picks the correct one."
          />
        </dl>

        <Rule />

        <div className="flex items-start gap-5">
          <SealMark className="mt-1 h-12 w-14 shrink-0 text-rule" />
          <div>
            <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
              Why {controls} of the ten have nothing wrong with them
            </h2>
            <p className="mt-2 max-w-[58ch] text-[0.9375rem] leading-relaxed text-ink-soft">
              A smoke alarm that goes off constantly catches every fire. It is also
              useless. If every file had a trap in it, an AI that said &ldquo;ask a
              human&rdquo; to everything would score full marks.
            </p>
            <p className="mt-3 max-w-[58ch] text-[0.9375rem] leading-relaxed text-ink-soft">
              So some files are clean, and raising a query on those counts against you. One
              of them genuinely has no claims, with a letter from the insurer confirming
              it. That looks almost identical to the file where the claims records are
              simply missing — and those two need opposite answers.
            </p>
          </div>
        </div>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          What happened
        </h2>
        {unbeaten.map((c) => (
          <div key={c.id} className="mt-4 border-l-2 border-stamp bg-stamp-wash px-5 py-4">
            <p className="text-[1.0625rem] leading-snug font-medium">
              Every model failed this one. Every single run.
            </p>
            <p className="mt-2.5 max-w-[60ch] text-[0.9375rem] leading-relaxed text-ink-soft">
              The file where the form says no claims and the records show two. All three
              models typed in &ldquo;2 claims&rdquo;, which is correct, and said honestly
              where they got it. None of them mentioned that the signed form said the
              opposite.
            </p>
            <p className="mt-2.5 max-w-[60ch] text-[0.9375rem] leading-relaxed text-ink-soft">
              One model even wrote the contradiction down in its notes, then filed the
              clean number anyway. Read what it said and it looks like it caught the
              problem. Read what it filed and the problem is invisible.
            </p>
            <div className="mt-3 font-mono text-micro text-stamp">
              {c.id} · {c.trials.length} runs, none passed
            </div>
          </div>
        ))}

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          Have a look around
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Card
            mark={<ScheduleMark className="h-7 w-8 text-rule" />}
            head="Live demo"
            body="Open any of the ten files, read the actual paperwork, then run it past a model right now and watch the twenty-one fields fill in one by one."
            hint="start with the file called “Form contradicts the loss runs”"
            onClick={() => onGo("live")}
          />
          <Card
            mark={<LedgerMark className="h-7 w-8 text-rule" />}
            head="Findings"
            body={`All ${data.totals.trials} runs that already happened. Every file, every model, and exactly which field went wrong.`}
            hint="red numbers are failures, so scan the column for them"
            onClick={() => onGo("recorded")}
          />
        </div>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          Things worth knowing
        </h2>
        <ul className="mt-4 space-y-3">
          {[
            "These files are made up. They show that a mistake like this can happen and can be caught, not how often it happens for real.",
            "The forms are modelled on the industry standard ones but they are not the real thing, because those are licensed.",
            `${data.totals.trials} runs over ten files is not enough to say one model is better than another, so there is no league table here.`,
            "I do not work in insurance. Every answer I marked as correct carries a link to where I got that from, so you can tell me I am wrong.",
          ].map((line) => (
            <li
              key={line}
              className="border-l-2 border-rule pl-4 text-[0.9375rem] leading-relaxed text-ink-soft"
            >
              {line}
            </li>
          ))}
        </ul>
      </article>
    </div>
  )
}

function Rule() {
  return <hr className="my-10 border-0 border-t border-rule-soft" />
}

function Step({
  mark,
  head,
  body,
  note,
}: {
  mark: React.ReactNode
  head: string
  body: string
  note?: string
}) {
  return (
    <li className="flex items-start gap-5">
      <span className="mt-0.5 shrink-0">{mark}</span>
      <div>
        <div className="text-[1rem] font-medium">{head}</div>
        <p className="mt-1 max-w-[56ch] text-[0.9375rem] leading-relaxed text-ink-soft">
          {body}
        </p>
        {note && (
          <p className="mt-2 max-w-[56ch] border-l-2 border-rule pl-3 text-[0.875rem] leading-relaxed text-ink-faint">
            {note}
          </p>
        )}
      </div>
    </li>
  )
}

function Check({ head, body }: { head: string; body: string }) {
  return (
    <div className="border-l-2 border-rule pl-4">
      <dt className="text-[1rem] font-medium">{head}</dt>
      <dd
        className="mt-1 max-w-[62ch] text-[0.9375rem] leading-relaxed text-ink-soft"
        dangerouslySetInnerHTML={{ __html: body }}
      />
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
      className="pressable rounded-control border border-rule bg-white px-5 py-4 text-left transition-colors hover:border-carbon"
    >
      <div className="flex items-center gap-2.5">
        {mark}
        <span className="text-[0.9375rem] font-medium">{head}</span>
      </div>
      <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-soft">{body}</p>
      <p className="mt-2.5 font-mono text-[0.6875rem] leading-relaxed text-carbon">
        {hint}
      </p>
    </button>
  )
}
