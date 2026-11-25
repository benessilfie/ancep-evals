import type { Answer } from "@/types"
import { money } from "@/components/RecordTable"
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

const RULE_WIDTHS = [68, 46, 34, 82, 40, 52, 28, 44, 44, 24, 58, 30, 36, 50, 50, 74, 46, 26, 48, 48, 38]

interface Props {
  answers: Map<string, Answer>
  running: boolean
}

export function BlankRecord({ answers, running }: Props) {
  const filled = answers.size
  const started = running || filled > 0

  return (
    <div>
      <div className="flex items-end justify-between gap-4 border-b border-rule pb-3">
        <div>
          <div className="text-[0.9375rem] font-semibold">
            {started ? "What it filed" : "Nothing has run yet"}
          </div>
          <p className="mt-0.5 text-[0.8125rem] text-ink-soft">
            {started
              ? `${filled} of ${RECORD_FIELDS.length} fields, each one carrying where it came from.`
              : `Twenty one fields, filled one at a time from the documents on the left.`}
          </p>
        </div>
        {running && (
          <span className="shrink-0 font-mono text-micro text-carbon">
            reading the documents…
          </span>
        )}
      </div>

      <table className="w-full border-collapse text-left">
        <tbody>
          {RECORD_FIELDS.map(({ field, label }, i) => {
            const answer = answers.get(field)
            return (
              <tr
                key={field}
                className="border-b border-rule-soft align-baseline transition-colors duration-500"
              >
                <td className="w-[9rem] py-2.5 pr-4 text-[0.8125rem] sm:w-[17rem]">
                  <span className={answer ? "text-ink" : "text-ink-faint"}>{label}</span>
                </td>
                <td className="py-2.5 pr-4">
                  {answer ? (
                    <span
                      className={cn(
                        "write-in block font-mono text-[0.75rem]",
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
                      className={cn("block h-px bg-rule-soft", running && "animate-pulse")}
                      style={{ width: `${RULE_WIDTHS[i]}%`, maxWidth: "22rem" }}
                    />
                  )}
                </td>
                <td className="hidden w-[6rem] py-2.5 pr-4 font-mono text-[0.75rem] text-ink-faint sm:table-cell">
                  {answer && answer.status !== "flagged" ? answer.mode : ""}
                </td>
                <td className="hidden w-[9rem] py-2.5 font-mono text-[0.75rem] text-ink-faint md:table-cell">
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
