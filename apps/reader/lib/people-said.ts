import { readFile } from 'node:fs/promises'
import path from 'node:path'

export type EvidenceLevel = 'direct_quote' | 'paraphrase' | 'inferred_impression'

export type PeopleSaidEntry = {
  id: string
  publicationDecisionId: string
  evidenceLevel: EvidenceLevel
  text: string
  speakerLabel: string | null
  occurredAt: string
  publishedAt: string
  context: string | null
  reaction: string | null
}

const DATA_ROOT = path.resolve(process.cwd(), '..', '..', 'data', 'public')
const PEOPLE_SAID_FILE = path.join(DATA_ROOT, 'social_mirror.jsonl')
const EVIDENCE_LEVELS = new Set<EvidenceLevel>([
  'direct_quote',
  'paraphrase',
  'inferred_impression',
])
const FORBIDDEN_PUBLIC_KEYS = new Set([
  'evidence',
  'source_object_id',
  'source_excerpt',
  'transcript',
  'speaker_entity_id',
])

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const isStringOrNull = (value: unknown): value is string | null =>
  typeof value === 'string' || value === null

const isIsoDateTime = (value: string) => !Number.isNaN(Date.parse(value))

export const parsePeopleSaidProjection = (value: unknown): PeopleSaidEntry | null => {
  if (!isObject(value)) return null
  if ([...FORBIDDEN_PUBLIC_KEYS].some(key => key in value)) return null

  const {
    claim_id,
    publication_decision_id,
    evidence_level,
    text,
    speaker_label,
    occurred_at,
    published_at,
    context = null,
    reaction = null,
  } = value

  if (typeof claim_id !== 'string' || claim_id.length === 0) return null
  if (
    typeof publication_decision_id !== 'string' ||
    publication_decision_id.length === 0
  ) {
    return null
  }
  if (
    typeof evidence_level !== 'string' ||
    !EVIDENCE_LEVELS.has(evidence_level as EvidenceLevel)
  ) {
    return null
  }
  if (typeof text !== 'string' || text.trim().length === 0) return null
  if (!isStringOrNull(speaker_label)) return null
  if (typeof occurred_at !== 'string' || !isIsoDateTime(occurred_at)) return null
  if (typeof published_at !== 'string' || !isIsoDateTime(published_at)) return null
  if (!isStringOrNull(context) || !isStringOrNull(reaction)) return null

  return {
    id: claim_id,
    publicationDecisionId: publication_decision_id,
    evidenceLevel: evidence_level as EvidenceLevel,
    text: text.trim(),
    speakerLabel: speaker_label,
    occurredAt: occurred_at,
    publishedAt: published_at,
    context,
    reaction,
  }
}

export const getPeopleSaidEntries = async (
  filePath = PEOPLE_SAID_FILE,
): Promise<PeopleSaidEntry[]> => {
  try {
    const raw = await readFile(filePath, 'utf8')
    const entries = raw
      .split(/\r?\n/)
      .filter(line => line.trim().length > 0)
      .map(line => {
        try {
          return parsePeopleSaidProjection(JSON.parse(line) as unknown)
        } catch {
          return null
        }
      })
      .filter((entry): entry is PeopleSaidEntry => entry !== null)

    return entries.sort((a, b) => b.occurredAt.localeCompare(a.occurredAt))
  } catch {
    return []
  }
}

export const evidenceLevelLabel = (level: EvidenceLevel) => {
  switch (level) {
    case 'direct_quote':
      return '逐語引用'
    case 'paraphrase':
      return '要約'
    case 'inferred_impression':
      return '推測'
  }
}

export const publicSpeakerLabel = (value: string | null) => {
  if (value === null) return '話者非公開'
  if (value === 'unknown') return '話者不明'
  return value
}
