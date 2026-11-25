import type { EvalCase } from "@/types"
import { cn } from "@/lib/utils"

const usd = (n: number) => `$${n.toLocaleString("en-US")}`

interface Side {
  source: string
  claim: string
  rows?: { left: string; mid?: string; right: string }[]
  quote?: string
  tone?: "stamp" | "neutral"
}

function sidesFor(evalCase: EvalCase): { lead: string; sides: Side[] } | null {
  const f = evalCase.facts
  if (!f) return null

  switch (evalCase.id) {
    case "05-application-contradicts-loss-runs":
      return {
        lead: "The client's signed form and the insurer's own records say different things.",
        sides: [
          {
            source: "On the form the client signed",
            claim: "No claims in the last five years",
            quote: "CHK HERE IF NONE  ☑",
            tone: "stamp",
          },
          {
            source: "In the claims records attached to the same email",
            claim: `${f.lossCount} claims, ${usd(f.totalIncurred)} in total`,
            rows: f.losses.map((l) => ({
              left: l.claimNo,
              mid: l.dateOfLoss,
              right: usd(l.incurred),
            })),
            tone: "stamp",
          },
        ],
      }
    case "04-stale-thread":
      return {
        lead: "The figure at the top of the email chain was corrected further down it.",
        sides: [
          {
            source: "Top of the thread, what you read first",
            claim: usd(7_900_000),
            quote: "Total sum insured across the schedule is $7,900,000.",
            tone: "stamp",
          },
          {
            source: "Three messages down, from the client",
            claim: usd(f.totalInsured),
            quote: `That takes the total sum insured to ${usd(f.totalInsured)}.`,
          },
        ],
      }
    case "07-loss-run-column-mislabel": {
      const row = f.losses.find((l) => l.reserved > 0)
      if (!row) return null
      return {
        lead: "On this carrier's layout the paid column does not add up.",
        sides: [
          {
            source: `Claim ${row.claimNo}, as printed`,
            claim: "Paid plus outstanding should equal incurred",
            rows: [
              { left: "loss paid", right: usd(row.incurred) },
              { left: "outstanding", right: usd(row.reserved) },
              { left: "total incurred", right: usd(row.incurred) },
            ],
            tone: "stamp",
          },
          {
            source: "What that means",
            claim: `${usd(row.incurred)} + ${usd(row.reserved)} is ${usd(row.incurred + row.reserved)}, not ${usd(row.incurred)}`,
            quote:
              "A column is mislabelled, so the paid figure cannot be trusted. Carriers name these columns differently.",
          },
        ],
      }
    }
    case "09-missing-loss-runs":
      return {
        lead: "The form points at a claims record that is not in the packet.",
        sides: [
          {
            source: "On the form",
            claim: "See attached loss summary",
            quote: "SEE ATTACHED LOSS SUMMARY  ☑",
            tone: "stamp",
          },
          {
            source: "In the packet",
            claim: "No claims record of any kind",
            quote:
              "Nothing attached, and no nil claims letter either. Absent is not the same as zero.",
            tone: "stamp",
          },
        ],
      }
    case "06-derived-total":
      return {
        lead: "No document in this packet states a total. It can only be added up.",
        sides: [
          {
            source: "What the agent must produce",
            claim: usd(f.totalInsured),
            quote: `The sum of ${f.locationCount} rows on the schedule of values.`,
          },
          {
            source: "What counts as wrong",
            claim: "Saying it read that off a form",
            quote:
              "The number is right either way. Claiming to have read it means nobody goes back and checks the arithmetic.",
            tone: "stamp",
          },
        ],
      }
    default:
      return null
  }
}

export function Evidence({ evalCase }: { evalCase: EvalCase }) {
  const content = sidesFor(evalCase)
  if (!content) return null

  return (
    <div className="shrink-0 border-b border-rule-soft bg-paper-sunk/50 px-6 py-5">
      <p className="text-[0.9375rem] leading-snug font-medium">{content.lead}</p>
      <div className="mt-4 grid gap-5 md:grid-cols-2">
        {content.sides.map((side) => (
          <div
            key={side.source}
            className={cn(
              "border-l-2 bg-white px-4 py-3",
              side.tone === "stamp" ? "border-stamp" : "border-rule"
            )}
          >
            <div className="field-label">{side.source}</div>
            <p
              className={cn(
                "mt-1.5 text-[1rem] leading-snug font-semibold",
                side.tone === "stamp" ? "text-stamp" : "text-ink"
              )}
            >
              {side.claim}
            </p>

            {side.rows && (
              <table className="mt-2.5 w-full border-collapse text-left">
                <tbody>
                  {side.rows.map((row) => (
                    <tr key={row.left} className="border-t border-rule-soft">
                      <td className="py-1.5 pr-3 font-mono text-[0.75rem] text-ink-soft">
                        {row.left}
                      </td>
                      {row.mid !== undefined && (
                        <td className="py-1.5 pr-3 font-mono text-[0.75rem] text-ink-soft">
                          {row.mid}
                        </td>
                      )}
                      <td className="py-1.5 text-right font-mono text-[0.75rem] tabular-nums">
                        {row.right}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {side.quote && (
              <p className="mt-2 font-mono text-[0.6875rem] leading-relaxed text-ink-faint">
                {side.quote}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
