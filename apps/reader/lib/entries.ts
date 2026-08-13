import { readFile, readdir } from 'node:fs/promises'
import path from 'node:path'

export type Entry = {
  id: string
  date: string
  imageUrl: string | null
  title: string
  content: string
}

const DATA_ROOT = path.resolve(process.cwd(), '..', '..', 'data')
const SUMMARY_DIR = path.join(DATA_ROOT, 'summaries')
const TRANSCRIPT_DIR = path.join(DATA_ROOT, 'transcripts')
const DAILY_STATE_FILE = path.join(DATA_ROOT, 'daily_state.json')
const MIN_PUBLISHABLE_BYTES = 50
const PUBLICATION_START_DATE = '2025-01-01'

const getSupabaseConfig = () => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

  return url && key ? { key, url } : null
}

type DailyStateEntry = {
  summary_source_files?: string[]
}

type DailyState = {
  dates?: Record<string, DailyStateEntry>
}

let dailyState: Promise<DailyState> | undefined

const readDailyState = () => {
  dailyState ??= readText(DAILY_STATE_FILE).then(value => JSON.parse(value) as DailyState)
  return dailyState
}

const isPublishableSummary = async (compactDate: string) => {
  const entry = (await readDailyState()).dates?.[compactDate]
  const sourceFiles = entry?.summary_source_files ?? []
  if (sourceFiles.length === 0) return false

  const sourceTexts = await Promise.all(
    sourceFiles.map(fileName =>
      readText(path.join(TRANSCRIPT_DIR, path.basename(fileName.replaceAll('\\', '/')))),
    ),
  )
  return (
    new TextEncoder().encode(sourceTexts.join('')).byteLength >
    MIN_PUBLISHABLE_BYTES
  )
}

const SUMMARY_FILE = /^(\d{8})_summary\.txt$/

const toDate = (compact: string) =>
  `${compact.slice(0, 4)}-${compact.slice(4, 6)}-${compact.slice(6, 8)}`

const readText = async (filePath: string) => readFile(filePath, 'utf8')

const parseTitle = (content: string) => {
  const firstLine = content.split(/\r?\n/, 1)[0]?.trim() ?? ''
  return firstLine.replaceAll('【', '').replaceAll('】', '') || 'Daily Summary'
}

const cleanContent = (content: string) => {
  const withoutTags = content.replace(/^tags:.*\r?\n?/gim, '').trim()
  const lines = withoutTags.split(/\r?\n/)
  const bodyStart = lines.findIndex((line, index) => index > 0 && line.trim() !== '')

  if (bodyStart === -1) {
    return lines.slice(1).join('\n').trim()
  }

  return lines.slice(bodyStart).join('\n').trim()
}

const readSummary = async (fileName: string): Promise<Entry | null> => {
  const match = fileName.match(SUMMARY_FILE)
  if (!match) return null
  if (!(await isPublishableSummary(match[1]))) return null

  const date = toDate(match[1])
  if (date < PUBLICATION_START_DATE) return null
  const content = await readText(path.join(SUMMARY_DIR, fileName))
  return {
    id: `summary:${date}`,
    date,
    imageUrl: null,
    title: parseTitle(content),
    content: cleanContent(content),
  }
}

type SupabaseEntry = {
  id: string
  date: string
  title: string
  content: string
  image_url: string | null
}

const fetchSupabase = async (query: Record<string, string>) => {
  const config = getSupabaseConfig()
  if (!config) return null

  const url = new URL(`${config.url.replace(/\/$/, '')}/rest/v1/daily_entries`)
  Object.entries(query).forEach(([name, value]) => url.searchParams.set(name, value))

  const response = await fetch(url, {
    headers: {
      apikey: config.key,
      Authorization: `Bearer ${config.key}`,
    },
    next: { revalidate: 300 },
  })

  if (!response.ok) {
    throw new Error(`Supabase request failed: ${response.status}`)
  }

  return (await response.json()) as SupabaseEntry[]
}

const getRemoteSummaries = async (): Promise<Entry[] | null> => {
  const rows = await fetchSupabase({
    select: 'id,date,title,content,image_url',
    is_public: 'eq.true',
    date: `gte.${PUBLICATION_START_DATE}`,
    order: 'date.desc',
  })

  return rows?.map(row => ({
    id: row.id,
    date: row.date,
    imageUrl: row.image_url,
    title: row.title,
    content: row.content,
  })) ?? null
}

export const formatDateOnly = (value: string) => {
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export const getLatestSummaries = async (limit?: number): Promise<Entry[]> => {
  const remoteSummaries = await getRemoteSummaries()
  if (remoteSummaries !== null) {
    return limit === undefined ? remoteSummaries : remoteSummaries.slice(0, limit)
  }

  try {
    const files = await readdir(SUMMARY_DIR)
    const summaries = await Promise.all(
      files
        .filter(fileName => SUMMARY_FILE.test(fileName))
        .sort((a, b) => b.localeCompare(a))
        .map(readSummary),
    )

    const published = summaries.filter(
      (entry): entry is Entry => entry !== null,
    )

    return limit === undefined ? published : published.slice(0, limit)
  } catch {
    return []
  }
}

export const getSummaryByDate = async (date: string): Promise<Entry | null> => {
  const remoteSummaries = await fetchSupabase({
    select: 'id,date,title,content,image_url',
    is_public: 'eq.true',
    date: `eq.${date}`,
    limit: '1',
  })
  if (remoteSummaries !== null) {
    const row = remoteSummaries[0]
    return row
      ? {
          id: row.id,
          date: row.date,
          imageUrl: row.image_url,
          title: row.title,
          content: row.content,
        }
      : null
  }

  try {
    return await readSummary(`${date.replaceAll('-', '')}_summary.txt`)
  } catch {
    return null
  }
}
