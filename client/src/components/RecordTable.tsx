import type { Answer, FieldVerdict, Trial } from "@/types"
import { cn } from "@/lib/utils"

const FIELD_LABELS: Record<string, string> = {
  applicant_name: "named insured",
  applicant_fein: "FEIN",
  applicant_entity_type: "entity type",
  mailing_address: "mailing address",
  business_started: "business started",
  annual_revenue_usd: "annual revenue",
  employee_count: "employees",
  policy_effective_date: "inception",
  policy_expiration_date: "expiry",
  location_count: "locations",
  total_insured_value_usd: "total sum insured",
  property_coinsurance_pct: "coinsurance",
  property_valuation_basis: "valuation basis",
  gl_each_occurrence_usd: "GL each occurrence",
  gl_general_aggregate_usd: "GL aggregate",
  prior_property_carrier: "expiring property carrier",
  loss_run_valuation_date: "loss run valuation date",
  loss_count_5y: "claims in 5 years",
  total_paid_5y_usd: "paid in 5 years",
  total_incurred_5y_usd: "incurred in 5 years",
  is_update_of_prior_submission: "update of an earlier submission",
}

export function money(value: string) {
  const digits = value.replace(/[^0-9-]/g, "")
  if (!digits || digits.length < 4 || !/^-?\d+$/.test(value.trim())) return value
  return Number(digits).toLocaleString("en-US")
}

export function RecordTable({ trial }: { trial: Trial }) {
  if (!trial.record) {
    return (
      <p className="p-5 text-[0.8125rem] text-ink-soft">
        No record was captured for this run.
      </p>
    )
  }
  const verdicts = new Map(trial.fields.map((f) => [f.field, f]))

  return (
    <table className="w-full border-collapse text-left">
      <thead className="sticky top-0 bg-white">
        <tr className="border-b border-rule">
          <th className="field-label px-5 py-2 font-normal">field</th>
          <th className="field-label px-3 py-2 font-normal">value</th>
          <th className="field-label hidden px-3 py-2 font-normal sm:table-cell">how</th>
          <th className="field-label hidden px-3 py-2 font-normal md:table-cell">from</th>
        </tr>
      </thead>
      <tbody>
        {Object.keys(FIELD_LABELS).map((field) => {
          const answer = trial.record?.[field] as Answer | undefined
          if (!answer) return null
          const verdict = verdicts.get(field)
          const bad = isBad(verdict)
          return (
            <tr
              key={field}
              className={cn("border-b border-rule-soft align-top", bad && "bg-stamp-wash")}
            >
              <td className="px-5 py-2 text-[0.8125rem]">
                {FIELD_LABELS[field]}
                <span className="block font-mono text-[0.625rem] text-ink-faint">
                  {field}
                </span>
              </td>
              <td
                className={cn(
                  "px-3 py-2 font-mono text-[0.75rem]",
                  bad ? "font-semibold text-stamp" : "text-ink"
                )}
              >
                {answer.status === "flagged" ? (
                  <span className="text-carbon">raised for a human</span>
                ) : (
                  money(answer.value)
                )}
                {bad && verdict && (
                  <span className="mt-1 block font-sans text-[0.75rem] font-normal text-stamp">
                    {humanise(verdict.detail)}
                  </span>
                )}
              </td>
              <td className="hidden px-3 py-2 font-mono text-[0.75rem] text-ink-soft sm:table-cell">
                {answer.status === "flagged" ? "" : answer.mode}
              </td>
              <td className="hidden px-3 py-2 font-mono text-[0.75rem] text-ink-soft md:table-cell">
                {answer.sources?.[0]?.document ?? ""}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function isBad(verdict: FieldVerdict | undefined) {
  if (!verdict) return false
  return (
    verdict.valueCorrect === false ||
    verdict.provenanceOk === false ||
    (verdict.flagDecision !== "correctly_flagged" &&
      verdict.flagDecision !== "correctly_not_flagged")
  )
}

export function humanise(detail: string) {
  const match = detail.match(/value='([^']*)'\s*wanted=(.+?);/)
  if (match) {
    const got = money(match[1])
    const want = money(match[2].replace(/^'|'$/g, ""))
    const rest = detail.split(";").slice(1).join(";").trim()
    const tail = rest && rest !== "ok" ? ` ${rest}` : ""
    return `Recorded ${got}. The packet says ${want}.${tail}`
  }
  if (detail.startsWith("flagged:")) {
    return detail.replace(/^flagged:\s*/, "Raised for a human: ")
  }
  return detail.replace(/;\s*ok$/, "")
}
