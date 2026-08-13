export const ARTIFACT_SEMANTICS = {
  diary: {
    label: 'DIARY / 日記',
    description:
      'その日の出来事を読み返すためにまとめた記録です。会話や写真などの元記録そのものではありません。',
  },
  novel: {
    label: 'NOVEL / 物語',
    archiveDescription:
      '日々の記憶をもとに、あとから物語として書いた創作です。事実記録としてではなく、記憶から派生したNarrative Artifactとして読める形で残しています。',
    detailDescription:
      'この文章は記憶をもとに後から物語として書いた創作です。日記や元の会話・写真そのものとは区別して読めるようにしています。',
  },
} as const
