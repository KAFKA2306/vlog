import { describe, expect, test } from 'bun:test'

import { groupTimelineArtifacts } from '../lib/timeline'

describe('Timeline grouping', () => {
  test('keeps same-day artifacts together and sorts newest first', () => {
    const days = groupTimelineArtifacts([
      {
        key: 'diary:1',
        kind: 'diary',
        label: 'Diary',
        title: 'A',
        text: 'A',
        imageUrl: null,
        href: '/day/2026-08-13',
        occurredAt: '2026-08-13T00:00:00',
      },
      {
        key: 'novel:1',
        kind: 'novel',
        label: 'Novel',
        title: 'B',
        text: 'B',
        imageUrl: null,
        href: '/novels/1',
        occurredAt: '2026-08-13T00:00:00',
      },
      {
        key: 'diary:2',
        kind: 'diary',
        label: 'Diary',
        title: 'C',
        text: 'C',
        imageUrl: null,
        href: '/day/2026-08-12',
        occurredAt: '2026-08-12T00:00:00',
      },
    ])

    expect(days.map(day => day.date)).toEqual(['2026-08-13', '2026-08-12'])
    expect(days[0].artifacts).toHaveLength(2)
  })
})
