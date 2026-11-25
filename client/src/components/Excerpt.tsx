import { cn } from "@/lib/utils"

interface Props {
  title: string
  body: string
  match: RegExp
  before?: number
  after?: number
  width?: number
  tone?: "neutral" | "stamp"
}

function columnOffset(lines: string[], hits: number[], width: number) {
  const starts = hits.map((i) => {
    const text = lines[i]
    if (text.length <= width) return 0
    const m = text.match(/\S/)
    const anchor = m?.index ?? 0
    return Math.max(0, Math.min(anchor - 2, text.length - width))
  })
  return Math.min(...starts, 0) === 0 ? Math.min(...starts) : 0
}

export function Excerpt({
  title,
  body,
  match,
  before = 1,
  after = 1,
  width = 62,
  tone = "neutral",
}: Props) {
  const lines = body.split("\n")
  const hits = lines.flatMap((line, i) => (match.test(line) ? [i] : []))
  if (hits.length === 0) return null

  const keep = new Set<number>()
  for (const hit of hits) {
    for (let i = hit - before; i <= hit + after; i++) {
      if (i >= 0 && i < lines.length) keep.add(i)
    }
  }
  const shown = [...keep].sort((a, b) => a - b)
  const offset = columnOffset(lines, hits, width)

  const crop = (text: string) => {
    const slice = text.slice(offset, offset + width)
    const truncated = text.length > offset + width
    return { slice: slice.trimEnd(), truncated }
  }

  return (
    <figure className="min-w-0">
      <figcaption className="border-b border-rule pb-1.5 font-mono text-[0.75rem]">
        {title}
      </figcaption>
      <div className="bg-white">
        <pre className="paper-doc overflow-hidden py-2.5 text-[0.6875rem] leading-[1.6]">
          {shown.map((index, position) => {
            const lit = hits.includes(index)
            const gap = position > 0 && index > shown[position - 1] + 1
            const { slice, truncated } = crop(lines[index])
            return (
              <span key={index} className="block">
                {gap && <span className="block px-3 text-rule select-none">···</span>}
                <span
                  className={cn(
                    "block px-3",
                    lit && tone === "stamp" && "bg-stamp-wash font-semibold text-stamp",
                    lit && tone === "neutral" && "bg-band font-semibold text-ink"
                  )}
                >
                  {slice || " "}
                  {truncated && <span className="text-rule">{" …"}</span>}
                </span>
              </span>
            )
          })}
        </pre>
      </div>
    </figure>
  )
}
