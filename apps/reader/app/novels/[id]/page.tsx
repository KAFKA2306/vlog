/* eslint-disable @next/next/no-img-element */

import Link from 'next/link'

import { formatDateOnly } from '@/lib/entries'
import { getPublicNovelById, getPublicNovels } from '@/lib/novels'

import styles from './page.module.css'

type Props = {
  params: Promise<{
    id: string
  }>
}

export async function generateStaticParams() {
  return (await getPublicNovels(60)).map(novel => ({ id: novel.id }))
}

export const dynamicParams = false

export default async function NovelPage({ params }: Props) {
  const { id } = await params
  const novel = await getPublicNovelById(id)

  return (
    <main className="page">
      <div className="wrap narrow">
        <Link className="back-link" href="/novels">
          ← 物語一覧
        </Link>

        {novel === null ? (
          <div className="empty-state">
            <h1>物語が見つかりません</h1>
            <p>公開対象のNovelとして取得できませんでした。</p>
          </div>
        ) : (
          <>
            <header className="day-header">
              <p className={styles.kind}>NOVEL / 物語</p>
              <h1 className="day-title">{novel.title}</h1>
              <time className="day-date" dateTime={novel.date}>
                {formatDateOnly(novel.date)}
              </time>
              <p className={styles.note}>
                この文章は記憶をもとに後から物語として書いた創作です。日記や元の会話・写真そのものとは区別して読めるようにしています。
              </p>
            </header>

            {novel.imageUrl ? (
              <figure className={styles.figure}>
                <img src={novel.imageUrl} alt="" loading="lazy" />
              </figure>
            ) : null}

            <article className="entry-copy">
              <p className="entry-body">{novel.content}</p>
            </article>
          </>
        )}
      </div>
    </main>
  )
}
