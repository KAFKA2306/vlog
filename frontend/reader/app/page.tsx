import Link from 'next/link'

import { formatDateOnly, getLatestSummaries } from '@/lib/entries'

export default async function Page() {
  const entries = await getLatestSummaries(60)

  return (
    <main className="page">
      <div className="wrap">
        <h1 className="site-title">VRChat Auto Diary</h1>

        {entries.length === 0 ? (
          <div className="empty-state">
            <p>No summaries found.</p>
          </div>
        ) : (
          <ol className="entries">
            {entries.map(entry => (
              <li key={entry.id}>
                <Link href={`/day/${entry.date}`} className="entry-link">
                  {formatDateOnly(entry.date)}
                </Link>
              </li>
            ))}
          </ol>
        )}
      </div>
    </main>
  )
}
