import { useCallback, useLayoutEffect, useRef, useState, type CSSProperties } from "react"

export function useMarker<T extends HTMLElement>(activeKey: string) {
  const track = useRef<T>(null)
  const [style, setStyle] = useState<CSSProperties>({ opacity: 0 })

  const place = useCallback(() => {
    const host = track.current
    const active = host?.querySelector<HTMLElement>('[data-on="true"]')
    if (!host || !active) return
    const base = host.getBoundingClientRect()
    const box = active.getBoundingClientRect()
    setStyle({
      transform: `translate(${box.left - base.left}px, ${box.top - base.top}px)`,
      width: box.width,
      height: box.height,
      opacity: 1,
    })
  }, [])

  useLayoutEffect(() => {
    place()
    const host = track.current
    if (!host) return
    const observer = new ResizeObserver(place)
    observer.observe(host)
    return () => observer.disconnect()
  }, [activeKey, place])

  return { track, style }
}
