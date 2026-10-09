import { describe, expect, test } from 'bun:test'

import { ARTIFACT_SEMANTICS } from '../lib/artifact-semantics'

describe('Diary and Novel semantics', () => {
  test('labels Diary and Novel as different artifact kinds', () => {
    expect(ARTIFACT_SEMANTICS.diary.label).toBe('DIARY / 日記')
    expect(ARTIFACT_SEMANTICS.novel.label).toBe('NOVEL / 物語')
  })

  test('does not present Diary as raw canonical evidence', () => {
    expect(ARTIFACT_SEMANTICS.diary.description).toContain('元記録そのものではありません')
  })

  test('explicitly presents Novel as a creative derivative rather than fact record', () => {
    expect(ARTIFACT_SEMANTICS.novel.archiveDescription).toContain('創作')
    expect(ARTIFACT_SEMANTICS.novel.archiveDescription).toContain('事実記録としてではなく')
    expect(ARTIFACT_SEMANTICS.novel.archiveDescription).toContain('Narrative Artifact')
    expect(ARTIFACT_SEMANTICS.novel.detailDescription).toContain('創作')
    expect(ARTIFACT_SEMANTICS.novel.detailDescription).toContain('日記や元の会話・写真そのものとは区別')
  })
})
