/**
 * Format break time descriptions for display
 * Handles complex break schedules with multiple shifts and periods
 *
 * Examples:
 * - "昼勤 10:30~10:40・12:40~13:20・15:20~15:30"
 * - "昼勤 10:30~10:40 / 夜勤 22:30~22:40"
 */

export interface FormattedBreakTime {
  shift: string  // e.g., "昼勤", "夜勤"
  periods: string[]  // e.g., ["10:30~10:40", "12:40~13:20"]
}

/**
 * Parse break time string into structured format
 */
export function parseBreakTime(breakTimeStr: string | null | undefined): FormattedBreakTime[] {
  if (!breakTimeStr) return []

  const result: FormattedBreakTime[] = []

  // Split by shifts (separated by / or 　 followed by shift keyword)
  const shiftPattern = /(昼勤|夜勤|日勤|早勤|遅勤|午前|午後)/g
  const matches = breakTimeStr.match(shiftPattern)

  if (!matches) {
    // No shift keywords found, treat entire string as single entry
    return [{
      shift: '休憩',
      periods: [breakTimeStr.trim()]
    }]
  }

  // Split by shift keywords
  const parts = breakTimeStr.split(shiftPattern).filter(p => p && p.trim())

  let currentShift = ''
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i].trim()

    // Check if this is a shift keyword
    if (/^(昼勤|夜勤|日勤|早勤|遅勤|午前|午後)$/.test(part)) {
      currentShift = part
    } else if (currentShift) {
      // This is the periods for the current shift
      // Split by ・ or / or multiple spaces
      const periods = part
        .split(/[・／/]/)
        .map(p => p.trim())
        .filter(p => p && p.length > 0)
        // Remove common separators and extra text
        .map(p => p
          .replace(/まで$/, '')
          .replace(/～/g, '~')
          .replace(/：/g, ':')
          .trim()
        )
        .filter(p => /\d/.test(p)) // Must contain at least one digit

      if (periods.length > 0) {
        result.push({
          shift: currentShift,
          periods
        })
      }
      currentShift = ''
    }
  }

  return result
}

/**
 * Format break time for display as React component-friendly array
 */
export function formatBreakTimeForDisplay(breakTimeStr: string | null | undefined): string[] {
  const parsed = parseBreakTime(breakTimeStr)

  if (parsed.length === 0) {
    return breakTimeStr ? [breakTimeStr] : []
  }

  const lines: string[] = []

  for (const { shift, periods } of parsed) {
    // Add shift header
    lines.push(`【${shift}】`)

    // Add each period on its own line with bullet
    for (const period of periods) {
      lines.push(`  • ${period}`)
    }
  }

  return lines
}

/**
 * Get total break minutes from break time string (best effort)
 */
export function calculateBreakMinutes(breakTimeStr: string | null | undefined): number {
  if (!breakTimeStr) return 0

  const parsed = parseBreakTime(breakTimeStr)
  let totalMinutes = 0

  for (const { periods } of parsed) {
    for (const period of periods) {
      // Try to extract time range like "10:30~10:40" or "10:30～10:40"
      const match = period.match(/(\d{1,2}):(\d{2})[~～](\d{1,2}):(\d{2})/)
      if (match) {
        const [, startH, startM, endH, endM] = match
        const startMinutes = parseInt(startH) * 60 + parseInt(startM)
        let endMinutes = parseInt(endH) * 60 + parseInt(endM)

        // Handle overnight periods (e.g., 23:00~01:00)
        if (endMinutes < startMinutes) {
          endMinutes += 24 * 60
        }

        totalMinutes += endMinutes - startMinutes
      }
    }
  }

  return totalMinutes
}
