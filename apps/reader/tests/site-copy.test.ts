import { describe, expect, test } from 'bun:test'

import { HOME_COPY } from '../lib/site-copy'

describe('KafLog home identity', () => {
  test('uses KafLog as the public Reader identity', () => {
    expect(HOME_COPY.eyebrow).toBe('KAFLOG')
    expect(HOME_COPY.title).toBe('KafLog')
  })

  test('explains the three ways of reading memory without technical framing', () => {
    expect(HOME_COPY.intro).toContain('日記')
    expect(HOME_COPY.intro).toContain('物語')
    expect(HOME_COPY.intro).toContain('人から言われたこと')
    expect(HOME_COPY.intro).toContain('公開を選んだ人生の断片')
  })

  test('does not restore the old AI-tool identity in hero copy', () => {
    const copy = JSON.stringify(HOME_COPY)

    expect(copy).not.toContain('VRChat Auto Diary')
    expect(copy).not.toContain('Gemini')
    expect(copy).not.toContain('Supabase')
    expect(copy).not.toContain('AI生成')
  })
})
