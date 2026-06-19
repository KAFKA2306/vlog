import { readFile, readdir } from 'node:fs/promises'
import path from 'node:path'

export type Entry = {
  id: string
  date: string
  title: string
  content: string
}

const DATA_ROOT = path.resolve(process.cwd(), '..', '..', 'data')
const SUMMARY_DIR = path.join(DATA_ROOT, 'summaries')

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
  const content = await readText(path.join(SUMMARY_DIR, fileName))
  return {
    id: `summary:${date}`,
    date,
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

export const getLatestSummaries = async (limit = 60): Promise<Entry[]> => {
  try {
    const files = await readdir(SUMMARY_DIR)
    const summaries = await Promise.all(
      files
        .filter(fileName => SUMMARY_FILE.test(fileName))
        .sort((a, b) => b.localeCompare(a))
        .slice(0, limit)
        .map(readSummary),
    )

    return summaries.filter((entry): entry is Entry => entry !== null)
  } catch {
    return []
  }
}

export const getSummaryByDate = async (date: string): Promise<Entry | null> => {
  try {
    return await readSummary(`${date.replaceAll('-', '')}_summary.txt`)
  } catch {
    return null
  }
}
