type MarkProps = { className?: string }

const base = "text-rule"

function Frame({ children, className }: MarkProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 64 52"
      aria-hidden
      className={className ?? `h-12 w-14 ${base}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
      strokeLinecap="square"
    >
      {children}
    </svg>
  )
}

export function PaperMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M8 14h30l8 8v22H8z" />
      <path d="M38 14v8h8" />
      <path d="M14 10h30l8 8v22" opacity=".55" />
      <path d="M20 6h30l8 8v22" opacity=".3" />
      <path d="M14 30h20M14 36h14" opacity=".8" />
    </Frame>
  )
}

export function FormMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M12 8h40v38H12z" />
      <path d="M12 18h40" opacity=".55" />
      <path d="M18 26h10M18 32h16M18 38h8" opacity=".8" />
      <path d="M40 26h6v6h-6z" />
      <path d="M41 29l2 2 3-4" opacity=".9" />
    </Frame>
  )
}

export function ScheduleMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M8 10h48v34H8z" />
      <path d="M8 18h48" opacity=".55" />
      <path d="M8 27h48M8 36h48" opacity=".35" />
      <path d="M24 10v34M40 10v34" opacity=".35" />
    </Frame>
  )
}

export function LedgerMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M10 10h44v34H10z" />
      <path d="M10 19h44" opacity=".55" />
      <path d="M10 28h44" opacity=".25" />
      <path d="M36 10v34" opacity=".35" />
      <path d="M14 24h14M14 33h10M40 24h10M40 33h6" opacity=".8" />
    </Frame>
  )
}

export function ThreadMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M8 10h34v20H8z" />
      <path d="M8 10l17 11 17-11" opacity=".7" />
      <path d="M22 24h34v20H22z" opacity=".6" />
      <path d="M22 24l17 11 17-11" opacity=".45" />
    </Frame>
  )
}

export function SealMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M12 8h40v38H12z" />
      <path d="M18 18h22M18 25h28M18 32h14" opacity=".7" />
      <circle cx="44" cy="37" r="7" opacity=".55" />
      <path d="M41 37l2 2 4-5" opacity=".8" />
    </Frame>
  )
}

export function VaultMark(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M10 12h44v30H10z" />
      <path d="M10 12l22 14 22-14" opacity=".4" />
      <circle cx="32" cy="30" r="6" opacity=".7" />
      <path d="M32 24v12M26 30h12" opacity=".4" />
    </Frame>
  )
}

export const GROUP_MARKS: Record<string, (p: MarkProps) => React.ReactElement> = {
  "what the carrier already holds": VaultMark,
  correspondence: ThreadMark,
  "the application": FormMark,
  schedules: ScheduleMark,
  "claims history": LedgerMark,
}

export const DOC_MARKS: Record<string, (p: MarkProps) => React.ReactElement> = {
  records_on_file: VaultMark,
  broker_email: ThreadMark,
  application: FormMark,
  property_section: FormMark,
  liability_section: FormMark,
  sov: ScheduleMark,
  loss_run_a: LedgerMark,
  loss_run_b: LedgerMark,
  no_losses_letter: SealMark,
}
