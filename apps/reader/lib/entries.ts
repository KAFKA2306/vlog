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
}

const DATA_ROOT = path.resolve(process.cwd(), '..', '..', 'data')
const SUMMARY_DIR = path.join(DATA_ROOT, 'summaries')
const TRANSCRIPT_DIR = path.join(DATA_ROOT, 'transcripts')
const DAILY_STATE_FILE = path.join(DATA_ROOT, 'daily_state.json')
const MIN_PUBLISHABLE_BYTES = 50

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
