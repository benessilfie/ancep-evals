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
      <article className="mx-auto w-full max-w-[52rem] px-6 py-12">
        <h1 className="max-w-[22ch] text-[2rem] leading-[1.12] font-semibold tracking-[-0.025em] sm:text-[2.5rem]">
          An eval set for submission intake, graded on the record rather than the
          summary.
        </h1>
        <p className="mt-6 max-w-[64ch] text-[1.0625rem] leading-relaxed text-ink-soft">
          Ten synthetic commercial submissions where every right answer is known before a
          model sees them. Three Claude models each read every packet three times. What
          gets scored is the structured record they filed, not the fluent paragraph they
          wrote about filing it.
        </p>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          Why the answers are free
        </h2>
        <p className="mt-2 max-w-[64ch] text-[0.9375rem] leading-relaxed text-ink-soft">
          Normally you would take real packets and pay someone who knows insurance to label
          them. Instead this works backwards.
        </p>
        <ol className="mt-6 space-y-5">
          <Step
            mark={<PaperMark className="h-10 w-12 text-rule" />}
            head="Write what is true first"
            body="One typed record describes the risk: the applicant, six locations and their values, two claims and what each cost."
          />
          <Step
            mark={<FormMark className="h-10 w-12 text-rule" />}
            head="Print the paperwork out of it"
            body="A broker's email thread, the application and its property and liability sections, a schedule of values, and loss runs from two carriers in deliberately different layouts."
          />
          <Step
            mark={<LedgerMark className="h-10 w-12 text-rule" />}
            head="Break exactly one thing"
            body="Tick the none box while the loss runs show two claims. Delete the total from every document. Split a location across a page break. The truth record still holds the right answer."
          />
        </ol>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          What gets checked
        </h2>
        <dl className="mt-5 grid gap-6 sm:grid-cols-3">
          <Check
            head="The value"
            body="Is the number right, compared after normalising dates, money and identifiers."
          />
          <Check
            head="The citation"
            body="It names a document and says whether it read the value or worked it out. If it claims to have read something, that value has to actually be in that document."
          />
          <Check
            head="The judgement"
            body="Where two documents disagree, or one is missing, the right answer is to stop and ask. Producing a confident number is the failure."
          />
        </dl>

        <Rule />

        <div className="flex items-start gap-5">
          <SealMark className="mt-1 h-12 w-14 shrink-0 text-rule" />
          <div>
            <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
              Why {controls} packets have nothing wrong with them
            </h2>
            <p className="mt-2 max-w-[60ch] text-[0.9375rem] leading-relaxed text-ink-soft">
              A smoke alarm that screams constantly catches every fire. If every packet
              needed flagging, an agent that flagged everything would score full marks and
              be useless. So some packets are clean, and raising a query on them counts
              against you. One of them has genuinely no claims with the carrier&rsquo;s nil
              letter attached, which looks identical to a packet with the claims record
              missing.
            </p>
          </div>
        </div>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">What it found</h2>
        {unbeaten.map((c) => (
          <div key={c.id} className="mt-4 border-l-2 border-stamp bg-stamp-wash px-5 py-4">
            <div className="font-mono text-micro text-stamp">
              {c.id} · no model passed, any run
            </div>
            <p className="mt-1.5 text-[1rem] leading-snug font-medium">{c.title}</p>
            <p className="mt-2 max-w-[62ch] text-[0.9375rem] leading-relaxed text-ink-soft">
              Every model produced the right claim count with an honest citation and no
              flag. One of them wrote the contradiction down in a free-text note and still
              filed a clean field. Read the transcript and it passed. Read the record and
              the conflict is invisible.
            </p>
          </div>
        ))}

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          Using this page
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => onGo("live")}
            className="pressable rounded-control border border-rule bg-white px-5 py-4 text-left transition-colors hover:border-carbon"
          >
            <div className="flex items-center gap-2.5">
              <ScheduleMark className="h-7 w-8 text-rule" />
              <span className="text-[0.9375rem] font-medium">Live demo</span>
            </div>
            <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-soft">
              Read any packet document by document, then run it against a model now and
              watch the record fill in. Or drop in your own files.
            </p>
          </button>
          <button
            type="button"
            onClick={() => onGo("recorded")}
            className="pressable rounded-control border border-rule bg-white px-5 py-4 text-left transition-colors hover:border-carbon"
          >
            <div className="flex items-center gap-2.5">
              <LedgerMark className="h-7 w-8 text-rule" />
              <span className="text-[0.9375rem] font-medium">Findings</span>
            </div>
            <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-soft">
              All {data.totals.trials} recorded runs. Every packet, every model, the record
              each one filed and exactly which field went wrong.
            </p>
          </button>
        </div>

        <Rule />

        <h2 className="text-[1.25rem] font-semibold tracking-[-0.01em]">
          What this is not
        </h2>
        <ul className="mt-4 space-y-2.5">
          {[
            "The packets are made up. They prove a failure can happen and is catchable, not how often it happens in production.",
            "The forms use industry field names but they are not ACORD forms, which are licensed.",
            `${data.totals.trials} runs over ten packets cannot rank models, so there is no score out of a hundred anywhere.`,
            "I do not work in insurance. Every expected answer carries a source you can argue with.",
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
}: {
  mark: React.ReactNode
  head: string
  body: string
}) {
  return (
    <li className="flex items-start gap-5">
      <span className="mt-0.5 shrink-0">{mark}</span>
      <div>
        <div className="text-[1rem] font-medium">{head}</div>
        <p className="mt-1 max-w-[58ch] text-[0.9375rem] leading-relaxed text-ink-soft">
          {body}
        </p>
      </div>
    </li>
  )
}

function Check({ head, body }: { head: string; body: string }) {
  return (
    <div className="border-t border-rule pt-3">
      <dt className="text-[0.9375rem] font-medium">{head}</dt>
      <dd className="mt-1.5 text-[0.8125rem] leading-relaxed text-ink-soft">{body}</dd>
    </div>
  )
}
