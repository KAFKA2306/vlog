import { describe, expect, test } from 'bun:test'

import {
  PUBLICATION_START_DATE,
  fetchAllPublicArchiveEntries,
  type PublicArchiveKind,
} from '../lib/public-archive'

type Row = {
  id: string
  date: string
  title: string
  content: string
  image_url: string | null
  is_public: boolean
}

const config = { url: 'https://example.invalid', key: '' }

const responseFor = (rows: Row[], offset: number, total: number) =>
  new Response(JSON.stringify(rows), {
    status: rows.length === total ? 200 : 206,
    headers: {
      'content-range':
        rows.length === 0 ? `*/${total}` : `${offset}-${offset + rows.length - 1}/${total}`,
    },
  })

const makeRows = (count: number, prefix = 'entry'): Row[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `${prefix}-${String(index).padStart(3, '0')}`,
    date: `2026-08-${String(31 - index).padStart(2, '0')}`,
    title: `${prefix} ${index}`,
    content: `content ${index}`,
    image_url: index % 2 === 0 ? null : `https://example.invalid/${prefix}-${index}.webp`,
    is_public: true,
  }))

const makePagedFetch = (rows: Row[]) => async (input: string | URL | Request) => {
  const url = input instanceof URL ? input : new URL(typeof input === 'string' ? input : input.url)
  const offset = Number(url.searchParams.get('offset') ?? '0')
  const limit = Number(url.searchParams.get('limit') ?? '250')
  expect(url.searchParams.get('is_public')).toBe('eq.true')
  expect(url.searchParams.get('date')).toBe(`gte.${PUBLICATION_START_DATE}`)
  expect(url.searchParams.get('order')).toBe('date.desc,id.asc')
  return responseFor(rows.slice(offset, offset + limit), offset, rows.length)
}

for (const kind of ['diary', 'novel'] as const satisfies readonly PublicArchiveKind[]) {
  describe(`${kind} public archive`, () => {
    test('retrieves every row exactly once across page sizes and accepts missing images', async () => {
      for (let count = 0; count <= 17; count += 1) {
        const rows = makeRows(count, kind)
        for (let pageSize = 1; pageSize <= 5; pageSize += 1) {
          const result = await fetchAllPublicArchiveEntries({
            config,
            fetchImpl: makePagedFetch(rows),
            kind,
            pageSize,
          })
          expect(result.map(entry => entry.id)).toEqual(rows.map(row => row.id))
          expect(new Set(result.map(entry => entry.id)).size).toBe(count)
          expect(result.length).toBe(count)
        }
      }
    })
  })
}

describe('public Reader fail-closed boundaries', () => {
  test('rejects a private row returned by the upstream service', async () => {
    const row = { ...makeRows(1)[0], is_public: false }
    await expect(
      fetchAllPublicArchiveEntries({
        config,
        fetchImpl: async () => responseFor([row], 0, 1),
        kind: 'diary',
        pageSize: 1,
      }),
    ).rejects.toThrow('Private row reached the public Reader boundary')
  })

  test('fixtures the publication boundary and rejects older rows', async () => {
    const row = { ...makeRows(1)[0], date: '2024-12-31' }
    expect(PUBLICATION_START_DATE).toBe('2025-01-01')
    await expect(
      fetchAllPublicArchiveEntries({
        config,
        fetchImpl: async () => responseFor([row], 0, 1),
        kind: 'novel',
        pageSize: 1,
      }),
    ).rejects.toThrow('Pre-publication row reached the public Reader boundary')
  })

  test('rejects duplicate rows across pages', async () => {
    const rows = makeRows(3)
    const fetchImpl = async (input: string | URL | Request) => {
      const url = input instanceof URL ? input : new URL(typeof input === 'string' ? input : input.url)
      const offset = Number(url.searchParams.get('offset') ?? '0')
      return offset === 0
        ? responseFor(rows.slice(0, 2), 0, 3)
        : responseFor([rows[1], rows[2]], 2, 3)
    }
    await expect(
      fetchAllPublicArchiveEntries({ config, fetchImpl, kind: 'diary', pageSize: 2 }),
    ).rejects.toThrow('Duplicate public Reader row across pages')
  })

  test('rejects a missing page instead of returning a partial archive', async () => {
    const rows = makeRows(4)
    const fetchImpl = async (input: string | URL | Request) => {
      const url = input instanceof URL ? input : new URL(typeof input === 'string' ? input : input.url)
      const offset = Number(url.searchParams.get('offset') ?? '0')
      return offset === 0 ? responseFor(rows.slice(0, 2), 0, 4) : responseFor([], offset, 4)
    }
    await expect(
      fetchAllPublicArchiveEntries({ config, fetchImpl, kind: 'diary', pageSize: 2 }),
    ).rejects.toThrow('Incomplete Supabase daily_entries pagination')
  })
})
