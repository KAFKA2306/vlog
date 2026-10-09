/* eslint-disable @next/next/no-img-element */

import Link from 'next/link'

import { formatDateOnly } from '@/lib/entries'
import { getTimelineDays } from '@/lib/timeline'

import styles from './page.module.css'

export default async function TimelinePage() {
  const days = await getTimelineDays()

  return (
    <main className="page">
      <div className="wrap narrow">
        <header className={styles.header}>
          <p className="eyebrow">TIMELINE / 個人史</p>
          <h1 className="day-title">同じ日を、ひとつの流れで読む</h1>
          <p className="site-intro">
            公開された日記、物語、人から言われたことを日付ごとにまとめています。
          </p>
        </header>

        {days.length === 0 ? (
          <div className="empty-state">
            <h2>まだ公開された記録はありません。</h2>
          </div>
        ) : (
          <ol className={styles.days}>
            {days.map(day => (
              <li key={day.date} className={styles.day}>
                <header className={styles.dayHeader}>
                  <time dateTime={day.date}>{formatDateOnly(day.date)}</time>
                  <span>{day.artifacts.length} records</span>
                </header>

                <ol className={styles.artifacts}>
                  {day.artifacts.map(artifact => {
                    const preview = artifact.text.replace(/\s+/g, ' ').slice(0, 180)
                    return (
                      <li key={artifact.key}>
                        <article
                          className={styles.artifact}
                          data-artifact-kind={artifact.kind}
                        >
                          <div className={styles.meta}>{artifact.label}</div>
                          <h2>{artifact.title}</h2>
                          <p>{preview}</p>
                          {artifact.imageUrl ? (
                            <figure className={styles.figure}>
                              <img src={artifact.imageUrl} alt="" loading="lazy" />
                            </figure>
                          ) : null}
                          <Link className={styles.link} href={artifact.href}>
                            この記録を読む →
                          </Link>
                        </article>
                      </li>
                    )
                  })}
                </ol>
              </li>
            ))}
          </ol>
        )}
      </div>
    </main>
  )
}
