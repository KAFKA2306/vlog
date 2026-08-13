export const PUBLICATION_START_DATE = '2025-01-01'
export const PUBLIC_ARCHIVE_PAGE_SIZE = 250

export type PublicArchiveKind = 'diary' | 'novel'

export type PublicArchiveEntry = {
  id: string
  date: string
  title: string
  content: string
  imageUrl: string | null
}

type SupabaseConfig = {
  url: string
  key: string
}

type SupabaseRow = {
  id: string
  date: string
  title: string
  content: string
  image_url?: string | null
  is_public: boolean
}

type FetchLike = (
  input: string | URL | Request,
  init?: RequestInit,
) => Promise<Response>

const TABLE_BY_KIND: Record<PublicArchiveKind, 'daily_entries' | 'novels'> = {
  diary: 'daily_entries',
  novel: 'novels',
}

export const getSupabaseConfig = (): SupabaseConfig | null => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

  return url && key ? { url, key } : null
}

const parseExactCount = (contentRange: string | null) => {
  const match = contentRange?.match(/\/(\d+)$/)
  if (!match) {
    throw new Error('Supabase response is missing an exact Content-Range count')
  }
  return Number(match[1])
}

const assertPublicRow = (row: SupabaseRow) => {
  if (row.is_public !== true) {
    throw new Error(`Private row reached the public Reader boundary: ${row.id}`)
  }
  if (row.date < PUBLICATION_START_DATE) {
    throw new Error(`Pre-publication row reached the public Reader boundary: ${row.id}`)
  }
}

const requestPage = async ({
  config,
  fetchImpl,
  kind,
  limit,
  offset,
}: {
  config: SupabaseConfig
  fetchImpl: FetchLike
  kind: PublicArchiveKind
  limit: number
  offset: number
}) => {
  const table = TABLE_BY_KIND[kind]
  const makeUrl = (withImage: boolean) => {
    const url = new URL(`${config.url.replace(/\/$/, '')}/rest/v1/${table}`)
    url.searchParams.set(
      'select',
      withImage
        ? 'id,date,title,content,image_url,is_public'
        : 'id,date,title,content,is_public',
    )
    url.searchParams.set('is_public', 'eq.true')
    url.searchParams.set('date', `gte.${PUBLICATION_START_DATE}`)
    url.searchParams.set('order', 'date.desc,id.asc')
    url.searchParams.set('limit', String(limit))
    url.searchParams.set('offset', String(offset))
    return url
  }

  const init: RequestInit = {
    headers: {
      apikey: config.key,
      Prefer: 'count=exact',
    },
    next: { revalidate: 300 },
  }

  let response = await fetchImpl(makeUrl(true), init)
  if (!response.ok && response.status === 400) {
    response = await fetchImpl(makeUrl(false), init)
  }
  if (!response.ok) {
    throw new Error(`Supabase ${table} request failed: ${response.status}`)
  }
  return response
}

export const fetchAllPublicArchiveEntries = async ({
  config,
  fetchImpl = fetch,
  kind,
  pageSize = PUBLIC_ARCHIVE_PAGE_SIZE,
}: {
  config: SupabaseConfig
  fetchImpl?: FetchLike
  kind: PublicArchiveKind
  pageSize?: number
}): Promise<PublicArchiveEntry[]> => {
  if (!Number.isInteger(pageSize) || pageSize <= 0) {
    throw new Error('pageSize must be a positive integer')
  }

  const table = TABLE_BY_KIND[kind]
  const entries: PublicArchiveEntry[] = []
  const seenIds = new Set<string>()
  let expectedTotal: number | null = null
  let offset = 0

  while (expectedTotal === null || entries.length < expectedTotal) {
    const response = await requestPage({
      config,
      fetchImpl,
      kind,
      limit: pageSize,
      offset,
    })

    const total = parseExactCount(response.headers.get('content-range'))
    if (expectedTotal === null) {
      expectedTotal = total
    } else if (total !== expectedTotal) {
      throw new Error(
        `Supabase ${table} count changed during pagination: ${expectedTotal} -> ${total}`,
      )
    }

    const rows = (await response.json()) as SupabaseRow[]
    if (rows.length > pageSize) {
      throw new Error(`Supabase ${table} returned more rows than requested`)
    }

    for (const row of rows) {
      assertPublicRow(row)
      if (seenIds.has(row.id)) {
        throw new Error(`Duplicate public Reader row across pages: ${row.id}`)
      }
      seenIds.add(row.id)
      entries.push({
        id: row.id,
        date: row.date,
        title: row.title,
        content: row.content,
        imageUrl: row.image_url ?? null,
      })
    }

    if (rows.length === 0) break
    offset += rows.length
  }

  if (expectedTotal === null || entries.length !== expectedTotal) {
    throw new Error(
      `Incomplete Supabase ${table} pagination: expected ${expectedTotal ?? 'unknown'}, got ${entries.length}`,
    )
  }

  return entries
}

export const getRemotePublicArchiveEntries = async (
  kind: PublicArchiveKind,
): Promise<PublicArchiveEntry[] | null> => {
  const config = getSupabaseConfig()
  if (!config) return null
  return fetchAllPublicArchiveEntries({ config, kind })
}
