import { afterEach, describe, expect, test } from 'bun:test'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'

import {
  evidenceLevelLabel,
  getPeopleSaidEntries,
  parsePeopleSaidProjection,
  publicSpeakerLabel,
} from '../lib/people-said'

const tempRoots: string[] = []

const makeTempFile = async (lines: unknown[]) => {
  const root = await mkdtemp(path.join(tmpdir(), 'kaflog-people-said-'))
  tempRoots.push(root)
  const filePath = path.join(root, 'social_mirror.jsonl')
  await writeFile(
    filePath,
    lines.map(line => JSON.stringify(line)).join('\n'),
    'utf8',
  )
  return filePath
}

const projection = (overrides: Record<string, unknown> = {}) => ({
  claim_id: '11111111-1111-4111-8111-111111111111',
  publication_decision_id: '22222222-2222-4222-8222-222222222222',
  evidence_level: 'direct_quote',
  text: '詳しすぎる',
  speaker_label: 'friend-a',
  occurred_at: '2026-08-01T12:00:00+09:00',
  published_at: '2026-08-13T19:00:00+09:00',
  context: 'VRChatで雑談中',
  reaction: '少し笑った',
  ...overrides,
})

afterEach(async () => {
  await Promise.all(tempRoots.splice(0).map(root => rm(root, { recursive: true })))
})

describe('People Said public projection', () => {
  test('maps only the public projection fields', () => {
    const entry = parsePeopleSaidProjection(projection())

    expect(entry).toEqual({
      id: '11111111-1111-4111-8111-111111111111',
      publicationDecisionId: '22222222-2222-4222-8222-222222222222',
      evidenceLevel: 'direct_quote',
      text: '詳しすぎる',
      speakerLabel: 'friend-a',
      occurredAt: '2026-08-01T12:00:00+09:00',
      publishedAt: '2026-08-13T19:00:00+09:00',
      context: 'VRChatで雑談中',
      reaction: '少し笑った',
    })
  })

  test('rejects any record carrying raw/private source fields', () => {
    for (const forbidden of [
      'evidence',
      'source_object_id',
      'source_excerpt',
      'transcript',
      'speaker_entity_id',
    ]) {
      expect(parsePeopleSaidProjection(projection({ [forbidden]: 'private' }))).toBeNull()
    }
  })

  test('keeps direct quote, paraphrase, and inference labels distinct', () => {
    expect(evidenceLevelLabel('direct_quote')).toBe('逐語引用')
    expect(evidenceLevelLabel('paraphrase')).toBe('要約')
    expect(evidenceLevelLabel('inferred_impression')).toBe('推測')
  })

  test('keeps speaker privacy states explicit', () => {
    expect(publicSpeakerLabel(null)).toBe('話者非公開')
    expect(publicSpeakerLabel('unknown')).toBe('話者不明')
    expect(publicSpeakerLabel('friend-a')).toBe('friend-a')
  })

  test('reads valid public rows, skips unsafe rows, and sorts by occurrence time', async () => {
    const filePath = await makeTempFile([
      projection({
        claim_id: '33333333-3333-4333-8333-333333333333',
        publication_decision_id: '44444444-4444-4444-8444-444444444444',
        evidence_level: 'paraphrase',
        occurred_at: '2026-08-02T10:00:00+09:00',
      }),
      projection({
        claim_id: '55555555-5555-4555-8555-555555555555',
        publication_decision_id: '66666666-6666-4666-8666-666666666666',
        transcript: 'raw transcript must not reach the Reader',
      }),
      projection({
        claim_id: '77777777-7777-4777-8777-777777777777',
        publication_decision_id: '88888888-8888-4888-8888-888888888888',
        evidence_level: 'inferred_impression',
        occurred_at: '2026-08-03T10:00:00+09:00',
        speaker_label: null,
        context: null,
        reaction: null,
      }),
    ])

    const entries = await getPeopleSaidEntries(filePath)

    expect(entries).toHaveLength(2)
    expect(entries.map(entry => entry.id)).toEqual([
      '77777777-7777-4777-8777-777777777777',
      '33333333-3333-4333-8333-333333333333',
    ])
  })

  test('returns an empty state for a missing projection file', async () => {
    const entries = await getPeopleSaidEntries('/definitely/missing/social_mirror.jsonl')
    expect(entries).toEqual([])
  })
})
