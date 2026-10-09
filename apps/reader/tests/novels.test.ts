import { afterEach, describe, expect, test } from 'bun:test'

import {
  getPublicNovels,
  novelPermalink,
  parsePublicNovel,
} from '../lib/novels'

const originalUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const originalKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

afterEach(() => {
  if (originalUrl === undefined) delete process.env.NEXT_PUBLIC_SUPABASE_URL
  else process.env.NEXT_PUBLIC_SUPABASE_URL = originalUrl

  if (originalKey === undefined) delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  else process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = originalKey
})

const publicRow = (overrides: Record<string, unknown> = {}) => ({
  id: '11111111-1111-4111-8111-111111111111',
  date: '2026-08-01',
  title: '記憶から生まれた物語',
  content: 'これは記憶をもとにした物語です。',
  tags: ['memory'],
  image_url: null,
  is_public: true,
  ...overrides,
})

describe('Novel public projection', () => {
  test('rejects explicitly private rows', () => {
    expect(parsePublicNovel(publicRow({ is_public: false }))).toBeNull()
  })

  test('maps optional public image without requiring it', () => {
    expect(parsePublicNovel(publicRow())?.imageUrl).toBeNull()
    expect(
      parsePublicNovel(
        publicRow({ image_url: 'https://example.invalid/public/novel.webp' }),
      )?.imageUrl,
    ).toBe('https://example.invalid/public/novel.webp')
  })

  test('uses the historical Novel id as the stable permalink key', () => {
    const id = '11111111-1111-4111-8111-111111111111'
    expect(novelPermalink(id)).toBe(`/novels/${id}`)
  })

  test('queries only public rows and deduplicates the canonical Novel id', async () => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://project.supabase.co'
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'public-anon-key'

    const calls: string[] = []
    const fetchMock = (async (input: RequestInfo | URL) => {
      calls.push(String(input))
      return new Response(JSON.stringify([publicRow(), publicRow()]), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    }) as typeof fetch

    const novels = await getPublicNovels(60, fetchMock)

    expect(novels).toHaveLength(1)
    expect(calls).toHaveLength(1)
    const url = new URL(calls[0])
    expect(url.pathname).toBe('/rest/v1/novels')
    expect(url.searchParams.get('is_public')).toBe('eq.true')
    expect(url.searchParams.get('order')).toBe('date.desc')
    expect(url.searchParams.get('limit')).toBe('60')
  })

  test('returns an empty public archive when Supabase public config is absent', async () => {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL
    delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

    const novels = await getPublicNovels()
    expect(novels).toEqual([])
  })
})
