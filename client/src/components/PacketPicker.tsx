import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { EvalCase } from "@/types"
import { cn } from "@/lib/utils"

export function PacketPicker({
  cases,
  selected,
  onSelect,
}: {
  cases: EvalCase[]
  selected: string
  onSelect: (id: string) => void
}) {
  return (
    <div className="shrink-0 border-b border-rule bg-paper-sunk/40 px-4 py-3 lg:hidden">
      <label className="field-label" htmlFor="packet-picker">
        packet
      </label>
      <Select value={selected} onValueChange={onSelect}>
        <SelectTrigger
          id="packet-picker"
          className="pressable mt-1.5 w-full rounded-field border border-rule bg-white px-2.5 py-2 text-left text-[0.8125rem]"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent
          position="popper"
          sideOffset={4}
          className="pop z-50 max-h-[22rem] w-[var(--radix-select-trigger-width)] overflow-y-auto rounded-field border border-rule bg-white p-1 shadow-[0_10px_30px_-14px_rgba(22,23,26,0.4)]"
        >
          {cases.map((c) => {
            const passed = c.trials.filter((t) => t.passed).length
            const none = passed === 0
            return (
              <SelectItem
                key={c.id}
                value={c.id}
                className="cursor-pointer rounded-field px-2.5 py-2 text-[0.8125rem] outline-none focus:bg-paper-sunk data-[state=checked]:bg-carbon-wash data-[state=checked]:font-medium data-[state=checked]:text-carbon"
              >
                <span className="flex w-full items-baseline gap-2">
                  <span className="font-mono text-[0.6875rem] text-ink-faint">
                    {c.id.slice(0, 2)}
                  </span>
                  <span className="min-w-0 flex-1 truncate">{c.short}</span>
                  <span
                    className={cn(
                      "shrink-0 font-mono text-[0.625rem]",
                      none ? "text-stamp" : "text-ink-faint"
                    )}
                  >
                    {passed}/{c.trials.length}
                  </span>
                </span>
              </SelectItem>
            )
          })}
        </SelectContent>
      </Select>
    </div>
  )
}
