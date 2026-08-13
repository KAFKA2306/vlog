export type PublicNovel = {
  id: string
  date: string
  title: string
  content: string
  tags: string[]
  imageUrl: string | null
}

type FetchLike = typeof fetch

const getSupabaseConfig = () => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.replace(/\/$/, '')
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  return url && key ? { url, key } : null
}

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

const fetchNovelRows = async (
  select: string,
  limit: number,
  fetchImpl: FetchLike,
): Promise<unknown[] | null> => {
  const config = getSupabaseConfig()
  if (!config) return null

  const params = new URLSearchParams({
    select,
    is_public: 'eq.true',
    order: 'date.desc',
    limit: String(limit),
  })
  const response = await fetchImpl(`${config.url}/rest/v1/novels?${params}`, {
    headers: {
      apikey: config.key,
      Authorization: `Bearer ${config.key}`,
    },
    cache: 'no-store',
  })
  if (!response.ok) return null

  const payload = (await response.json()) as unknown
  return Array.isArray(payload) ? payload : null
}

export const getPublicNovels = async (
  limit = 60,
  fetchImpl: FetchLike = fetch,
): Promise<PublicNovel[]> => {
  const preferred = await fetchNovelRows(
    'id,date,title,content,tags,image_url,is_public',
    limit,
    fetchImpl,
  )
  const rows =
    preferred ??
    (await fetchNovelRows('id,date,title,content,tags,is_public', limit, fetchImpl))

  if (rows === null) return []

  const seen = new Set<string>()
  return rows.flatMap(row => {
    const novel = parsePublicNovel(row)
    if (novel === null || seen.has(novel.id)) return []
    seen.add(novel.id)
    return [novel]
  })
}

export const getPublicNovelById = async (id: string): Promise<PublicNovel | null> => {
  const novels = await getPublicNovels(60)
  return novels.find(novel => novel.id === id) ?? null
}
