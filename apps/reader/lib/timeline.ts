import { diaryPermalink, getLatestSummaries, type Entry } from './entries'
import {
  getPublicNovels,
  novelPermalink,
  type PublicNovel,
} from './novels'
import {
  evidenceLevelLabel,
  getPeopleSaidEntries,
  publicSpeakerLabel,
  type PeopleSaidEntry,
} from './people-said'

export type TimelineArtifactKind = 'diary' | 'novel' | 'people-said'

export type TimelineArtifact = {
  key: string
  kind: TimelineArtifactKind
  label: string
  title: string
  text: string
  imageUrl: string | null
  href: string
  occurredAt: string
}

export type TimelineDay = {
  date: string
  artifacts: TimelineArtifact[]
}

export const groupTimelineArtifacts = (
  artifacts: TimelineArtifact[],
): TimelineDay[] => {
  const byDate = new Map<string, TimelineArtifact[]>()

  for (const artifact of artifacts) {
    const date = artifact.occurredAt.slice(0, 10)
    const current = byDate.get(date)
    if (current) current.push(artifact)
    else byDate.set(date, [artifact])
  }

  return [...byDate.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .map(([date, dayArtifacts]) => ({
      date,
      artifacts: dayArtifacts.sort((left, right) => {
        const order = right.occurredAt.localeCompare(left.occurredAt)
        return order === 0 ? left.key.localeCompare(right.key) : order
      }),
    }))
}

const fromDiary = (entry: Entry): TimelineArtifact => ({
  key: `diary:${entry.id}`,
  kind: 'diary',
  label: 'Diary / 日記',
  title: entry.title,
  text: entry.content,
  imageUrl: entry.imageUrl,
  href: diaryPermalink(entry.date),
  occurredAt: `${entry.date}T00:00:00`,
})

const fromNovel = (entry: PublicNovel): TimelineArtifact => ({
  key: `novel:${entry.id}`,
  kind: 'novel',
  label: 'Novel / 物語',
  title: entry.title,
  text: entry.content,
  imageUrl: entry.imageUrl,
  href: novelPermalink(entry.id),
  occurredAt: `${entry.date}T00:00:00`,
})

const fromPeopleSaid = (entry: PeopleSaidEntry): TimelineArtifact => ({
  key: `people-said:${entry.id}:${entry.publicationDecisionId}`,
  kind: 'people-said',
  label: `People Said / ${evidenceLevelLabel(entry.evidenceLevel)}`,
  title: publicSpeakerLabel(entry.speakerLabel),
  text: entry.text,
  imageUrl: null,
  href: '/people-said',
  occurredAt: entry.occurredAt,
})

export const buildTimelineDays = ({
  diaries,
  novels,
  peopleSaid,
}: {
  diaries: Entry[]
  novels: PublicNovel[]
  peopleSaid: PeopleSaidEntry[]
}) =>
  groupTimelineArtifacts([
    ...diaries.map(fromDiary),
    ...novels.map(fromNovel),
    ...peopleSaid.map(fromPeopleSaid),
  ])

export const getTimelineDays = async (): Promise<TimelineDay[]> => {
  const [diaries, novels, peopleSaid] = await Promise.all([
    getLatestSummaries(),
    getPublicNovels(),
    getPeopleSaidEntries(),
  ])
  return buildTimelineDays({ diaries, novels, peopleSaid })
}
