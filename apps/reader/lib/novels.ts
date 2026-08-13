import {
  fetchAllPublicArchiveEntries,
  getSupabaseConfig,
} from './public-archive'

export type PublicNovel = {
  id: string
  date: string
  title: string
  content: string
  tags: string[]
  imageUrl: string | null
}

type FetchLike = typeof fetch

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const parseTags = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.filter((tag): tag is string => typeof tag === 'string')
    : []

export const novelPermalink = (id: string) => `/novels/${encodeURIComponent(id)}`

export const parsePublicNovel = (value: unknown): PublicNovel | null => {
  if (!isObject(value)) return null

  const { id, date, title, content, tags = [], image_url = null, is_public } = value

  if (is_public === false) return null
  if (typeof id !== 'string' || id.length === 0) return null
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return null
  if (typeof title !== 'string' || title.trim().length === 0) return null
  if (typeof content !== 'string' || content.trim().length === 0) return null
  if (image_url !== null && typeof image_url !== 'string') return null

  return {
    id,
    date,
    title: title.trim(),
    content: content.trim(),
    tags: parseTags(tags),
    imageUrl: image_url,
  }
}

export const getPublicNovels = async (
  _legacyLimit?: number,
  fetchImpl: FetchLike = fetch,
): Promise<PublicNovel[]> => {
  const config = getSupabaseConfig()
  if (!config) return []

  const entries = await fetchAllPublicArchiveEntries({
    config,
    fetchImpl,
    kind: 'novel',
  })
  return entries.map(entry => ({ ...entry, tags: [] }))
}

export const getPublicNovelById = async (id: string): Promise<PublicNovel | null> => {
  const novels = await getPublicNovels()
  return novels.find(novel => novel.id === id) ?? null
}
