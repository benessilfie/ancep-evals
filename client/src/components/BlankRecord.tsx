import type { Answer } from "@/types"
import { money } from "@/components/RecordTable"
import { PaperMark } from "@/components/Marks"
import { cn } from "@/lib/utils"

export const RECORD_FIELDS: { field: string; label: string }[] = [
  { field: "applicant_name", label: "named insured" },
  { field: "applicant_fein", label: "FEIN" },
  { field: "applicant_entity_type", label: "entity type" },
  { field: "mailing_address", label: "mailing address" },
  { field: "business_started", label: "business started" },
  { field: "annual_revenue_usd", label: "annual revenue" },
  { field: "employee_count", label: "employees" },
  { field: "policy_effective_date", label: "inception" },
  { field: "policy_expiration_date", label: "expiry" },
  { field: "location_count", label: "locations" },
  { field: "total_insured_value_usd", label: "total sum insured" },
  { field: "property_coinsurance_pct", label: "coinsurance" },
  { field: "property_valuation_basis", label: "valuation basis" },
  { field: "gl_each_occurrence_usd", label: "GL each occurrence" },
  { field: "gl_general_aggregate_usd", label: "GL aggregate" },
  { field: "prior_property_carrier", label: "expiring property carrier" },
  { field: "loss_run_valuation_date", label: "loss run valuation date" },
  { field: "loss_count_5y", label: "claims in 5 years" },
  { field: "total_paid_5y_usd", label: "paid in 5 years" },
  { field: "total_incurred_5y_usd", label: "incurred in 5 years" },
  { field: "is_update_of_prior_submission", label: "update of an earlier submission" },
]

interface Props {
  answers: Map<string, Answer>
  running: boolean
}

export function BlankRecord({ answers, running }: Props) {
  const filled = answers.size
  const started = running || filled > 0

  if (!started) {
    return (
      <div className="max-w-[46rem]">
        <PaperMark className="h-14 w-16 text-rule" />
        <h3 className="mt-4 text-[1.0625rem] font-semibold">The record</h3>
        <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-soft">
          This is what the agent hands over: twenty-one fields that a broker&rsquo;s system
          stores and an underwriter prices from. Every field carries the value, whether the
          agent read it or worked it out, and which document it came from.
        </p>
        <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink-soft">
          It is the only thing worth grading. A model that gets this wrong will still
          describe its work in fluent, confident prose.
        </p>
        <p className="mt-5 font-mono text-micro text-ink-faint">
          press run and the fields fill in one at a time
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-end justify-between gap-4 border-b border-rule pb-3">
        <div className="flex items-center gap-3">
          <PaperMark />
          <div>
            <div className="text-[0.9375rem] font-semibold">The record</div>
            <p className="mt-0.5 text-[0.8125rem] text-ink-soft">
              {filled} of {RECORD_FIELDS.length} fields filled.
            </p>
          </div>
        </div>
        {running && (
          <span className="font-mono text-micro text-carbon">reading the documents…</span>
        )}
      </div>

      <table className="w-full border-collapse text-left">
        <tbody>
          {RECORD_FIELDS.map(({ field, label }) => {
            const answer = answers.get(field)
            return (
              <tr
                key={field}
                className={cn(
                  "border-b border-rule-soft align-baseline transition-colors duration-500",
                  answer ? "bg-transparent" : "bg-paper-sunk/30"
                )}
              >
                <td className="w-[17rem] py-2.5 pr-4 text-[0.8125rem]">
                  <span className={answer ? "text-ink" : "text-ink-faint"}>{label}</span>
                </td>
                <td className="py-2.5 pr-4">
                  {answer ? (
                    <span
                      className={cn(
                        "font-mono text-[0.75rem] duration-500 animate-in fade-in",
                        answer.status === "flagged"
                          ? "font-medium text-carbon"
                          : "text-ink"
                      )}
                    >
                      {answer.status === "flagged"
                        ? "raised for a human"
                        : money(answer.value)}
                    </span>
                  ) : (
                    <span
                      aria-hidden
                      className="block h-px w-full max-w-[22rem] bg-rule-soft"
                    />
                  )}
                </td>
                <td className="w-[6rem] py-2.5 pr-4 font-mono text-[0.75rem] text-ink-faint">
                  {answer ? (answer.status === "flagged" ? "—" : answer.mode) : ""}
                </td>
                <td className="w-[9rem] py-2.5 font-mono text-[0.75rem] text-ink-faint">
                  {answer?.sources?.[0]?.document ?? ""}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
