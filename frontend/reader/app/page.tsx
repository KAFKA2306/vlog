'use client'

import { useEffect, useState } from 'react'
import { getSupabase } from '@/lib/supabaseClient'

type Entry = { id: string; date: string; title: string; content: string; tags: string[] | null }

const Tags = ({ tags }: { tags: string[] }) => (
  <div className="tags">{tags.map(t => <span key={t}>#{t}</span>)}</div>
)

export default function Page() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [selected, setSelected] = useState<Entry>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const [search, setSearch] = useState('')

  const fetchEntries = async () => {
    setLoading(true)
    setError(undefined)
    const supabase = getSupabase()
    if (!supabase) {
      setError('Supabase not configured')
      setLoading(false)
      return
    }
    const { data, error: fetchError } = await supabase
      .from('daily_entries')
      .select('id,date,title,content,tags')
      .eq('is_public', true)
      .order('date', { ascending: false })
      .limit(120)
    if (fetchError) {
      setError(fetchError.message)
    } else {
      setEntries((data as Entry[]) ?? [])
    }
    setLoading(false)
  }

  useEffect(() => { fetchEntries() }, [])

  const filteredEntries = search
    ? entries.filter(e =>
      e.title.toLowerCase().includes(search.toLowerCase()) ||
      e.content.toLowerCase().includes(search.toLowerCase()) ||
      e.tags?.some(t => t.toLowerCase().includes(search.toLowerCase()))
    )
    : entries

  return (
    <main className="page">
      <div className="wrap">
        <header className="hero">
          <div>
            <p className="eyebrow">VRChat Auto Diary</p>
            <h1>KAFKA Log</h1>
            <p className="muted">毎日の VR 空間をすぐ読めるミニマルビュー。</p>
          </div>
          <div className="halo" />
        </header>

        <div className="search-bar">
          <input
            type="text"
            placeholder="🔍 Search diaries..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
          {search && (
            <button className="ghost clear-btn" onClick={() => setSearch('')}>
              Clear
            </button>
          )}
        </div>

        {loading && (
          <div className="list">
            {[1, 2, 3].map(i => (
              <div key={i} className="entry skeleton">
                <div className="skeleton-line" />
                <div className="skeleton-line short" />
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="empty-state">
            <p>❌ {error}</p>
            <button className="ghost" onClick={fetchEntries}>再試行</button>
          </div>
        )}

        {!loading && !error && filteredEntries.length === 0 && (
          <div className="empty-state">
            <p>{search ? `🔍 "${search}" に一致する日記がありません` : '📝 まだ日記がありません'}</p>
          </div>
        )}

        {!loading && !error && filteredEntries.length > 0 && (
          <div className="list">
            {filteredEntries.map(e => (
              <button key={e.id} className="entry" onClick={() => setSelected(e)}>
                <div className="meta">
                  <span>{new Date(e.date).toLocaleDateString()}</span>
                  <span className="dot" />
                  <span>{(e.tags ?? []).slice(0, 2).join(' · ') || 'untagged'}</span>
                </div>
                <h3>{e.title}</h3>
                <p className="preview">{e.content}</p>
                {e.tags?.length ? <Tags tags={e.tags} /> : null}
              </button>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <section className="overlay" onClick={() => setSelected(undefined)}>
          <article className="sheet" onClick={e => e.stopPropagation()}>
            <header className="sheet-head">
              <div>
                <p className="muted">{new Date(selected.date).toLocaleDateString()}</p>
                <h2>{selected.title}</h2>
              </div>
              <button className="ghost" onClick={() => setSelected(undefined)}>閉じる</button>
            </header>
            <p className="content">{selected.content}</p>
            {selected.tags?.length ? <Tags tags={selected.tags} /> : null}
          </article>
        </section>
      )}
    </main>
  )
}
