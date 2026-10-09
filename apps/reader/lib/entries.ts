import { readFile, readdir } from 'node:fs/promises'
import path from 'node:path'

import {
  PUBLICATION_START_DATE,
  getRemotePublicArchiveEntries,
} from './public-archive'

export type Entry = {
  id: string
  date: string
  imageUrl: string | null
  title: string
  content: string
  source?: 'summary' | 'novel'
}

const DATA_ROOT = path.resolve(process.cwd(), '..', '..', 'data')
const SUMMARY_DIR = path.join(DATA_ROOT, 'summaries')
const TRANSCRIPT_DIR = path.join(DATA_ROOT, 'transcripts')
const DAILY_STATE_FILE = path.join(DATA_ROOT, 'daily_state.json')
const MIN_PUBLISHABLE_BYTES = 50

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

  const date = toDate(match[1])
  if (date < PUBLICATION_START_DATE) return null
  if (!(await isPublishableSummary(match[1]))) return null

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

const fetchSupabase = async (
  table: 'daily_entries' | 'novels',
  query: Record<string, string>,
) => {
  const config = getSupabaseConfig()
  if (!config) return null

  const url = new URL(`${config.url.replace(/\/$/, '')}/rest/v1/${table}`)
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

const getRemoteEntries = async (
  table: 'daily_entries' | 'novels',
  source: EntrySource,
): Promise<Entry[] | null> => {
  const pageSize = 100
  const rows: SupabaseEntry[] = []
  let offset = 0

  while (true) {
    const page = await fetchSupabase(table, {
      select: 'id,date,title,content,image_url',
      is_public: 'eq.true',
      date: `gte.${PUBLICATION_START_DATE}`,
      order: 'date.desc',
      limit: String(pageSize),
      offset: String(offset),
    })

    if (page === null) return null
    rows.push(...page)
    if (page.length < pageSize) break
    offset += pageSize
  }

  return rows.map(row => ({
    id: row.id,
    date: row.date,
    imageUrl: row.image_url,
    source,
    title: row.title,
    content: row.content,
  })) ?? null
}

const getRemoteSummaries = () => getRemoteEntries('daily_entries', 'summary')

const getRemoteNovels = () => getRemoteEntries('novels', 'novel')

export const formatDateOnly = (value: string) => {
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export const diaryPermalink = (date: string) => `/day/${encodeURIComponent(date)}`

export const getLatestSummaries = async (_limit?: number): Promise<Entry[]> => {
  const remoteEntries = await getRemotePublicArchiveEntries('diary')
  if (remoteEntries !== null) return remoteEntries

  try {
    const files = await readdir(SUMMARY_DIR)
    const summaries = await Promise.all(
      files
        .filter(fileName => SUMMARY_FILE.test(fileName))
        .sort((a, b) => b.localeCompare(a))
        .map(readSummary),
    )
    return summaries.filter((entry): entry is Entry => entry !== null)
  } catch {
    return []
  }
}

export const getPublishedEntries = async (): Promise<Entry[]> => {
  const [summaries, novels] = await Promise.all([
    getRemoteSummaries(),
    getRemoteNovels(),
  ])

  if (summaries === null || novels === null) return getLatestSummaries()

  return [...summaries, ...novels].sort(
    (left, right) =>
      new Date(right.date).getTime() - new Date(left.date).getTime(),
  )
}

export const getSummaryByDate = async (date: string): Promise<Entry | null> => {
  if (date < PUBLICATION_START_DATE) return null

  const remoteEntries = await getRemotePublicArchiveEntries('diary')
  if (remoteEntries !== null) {
    return remoteEntries.find(entry => entry.date === date) ?? null
  }

  try {
    return await readSummary(`${date.replaceAll('-', '')}_summary.txt`)
  } catch {
    return null
  }
}

export const getEntryById = async (id: string): Promise<Entry | null> => {
  const [summaries, novels] = await Promise.all([
    fetchSupabase('daily_entries', {
      select: 'id,date,title,content,image_url',
      is_public: 'eq.true',
      id: `eq.${id}`,
      limit: '1',
    }),
    fetchSupabase('novels', {
      select: 'id,date,title,content,image_url',
      is_public: 'eq.true',
      id: `eq.${id}`,
      limit: '1',
    }),
  ])

  const row = summaries?.[0]
  if (row) {
    return {
      id: row.id,
      date: row.date,
      imageUrl: row.image_url,
      source: 'summary',
      title: row.title,
      content: row.content,
    }
  }

  const novel = novels?.[0]
  if (novel) {
    return {
      id: novel.id,
      date: novel.date,
      imageUrl: novel.image_url,
      source: 'novel',
      title: novel.title,
      content: novel.content,
    }
  }

  if (summaries === null && novels === null && id.startsWith('summary:')) {
    return getSummaryByDate(id.slice('summary:'.length))
  }

  return null
}
