'use client'

import { useEffect, useState } from 'react'
import { getSupabase } from '@/lib/supabaseClient'

type Entry = {
  id: string
  date: string
  title: string
  content: string
  tags: string[] | null
  source: 'summary' | 'novel'
}

const Tags = ({ tags, source }: { tags: string[], source: 'summary' | 'novel' }) => (
  <div className="tags">
    {source === 'novel' && <span className="tag-novel">#小説</span>}
    {tags.map(t => <span key={t}>#{t}</span>)}
  </div>
)

export default function Page() {
  const [entries, setEntries] = useState<Entry[]>([])
  const [selected, setSelected] = useState<Entry>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'summary' | 'novel'>('all')

  const fetchEntries = async () => {
    setLoading(true)
    setError(undefined)
    const supabase = getSupabase()
    if (!supabase) {
      setError('Supabase not configured')
      setLoading(false)
      return
    }

    try {
      const [summariesResult, novelsResult] = await Promise.all([
        supabase
          .from('daily_entries')
          .select('id,date,title,content,tags')
          .eq('is_public', true)
          .order('date', { ascending: false })
          .limit(60),
        supabase
          .from('novels')
          .select('id,date,title,content,tags')
          .eq('is_public', true)
          .order('date', { ascending: false })
          .limit(60)
      ])

      if (summariesResult.error) throw summariesResult.error
      if (novelsResult.error) throw novelsResult.error

      const summaries = (summariesResult.data || []).map(e => ({ ...e, source: 'summary' } as Entry))
      const novels = (novelsResult.data || []).map(e => ({ ...e, source: 'novel' } as Entry))

      const allEntries = [...summaries, ...novels].sort((a, b) =>
        new Date(b.date).getTime() - new Date(a.date).getTime()
      )

      setEntries(allEntries)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchEntries() }, [])

  const filteredEntries = entries.filter(e => {
    const matchesSearch = search
      ? e.title.toLowerCase().includes(search.toLowerCase()) ||
      e.content.toLowerCase().includes(search.toLowerCase()) ||
      e.tags?.some(t => t.toLowerCase().includes(search.toLowerCase()))
      : true

    const matchesFilter = filter === 'all' || e.source === filter

    return matchesSearch && matchesFilter
  })

  return (
    <main className="page">
      <div className="wrap">
        <header className="hero">
          <div>
            <p className="eyebrow">VRChat Auto Diary</p>
            <h1>KAFKA Log & Novels</h1>
            <p className="muted">毎日の VR 空間をすぐ読めるミニマルビュー。</p>
          </div>
          <div className="halo" />
        </header>

        <div className="controls">
          <div className="search-bar">
            <input
              type="text"
              placeholder="🔍 Search..."
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

          <div className="filter-tabs">
            <button
              className={`tab ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            <button
              className={`tab ${filter === 'summary' ? 'active' : ''}`}
              onClick={() => setFilter('summary')}
            >
              Summaries
            </button>
            <button
              className={`tab ${filter === 'novel' ? 'active' : ''}`}
              onClick={() => setFilter('novel')}
            >
              Novels
            </button>
          </div>
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
            <p>{search ? `🔍 "${search}" に一致するエントリーがありません` : '📝 まだエントリーがありません'}</p>
          </div>
        )}

        {!loading && !error && filteredEntries.length > 0 && (
          <div className="list">
            {filteredEntries.map(e => (
              <button key={e.id} className={`entry ${e.source}`} onClick={() => setSelected(e)}>
                <div className="meta">
                  <span>{new Date(e.date).toLocaleDateString()}</span>
                  <span className="dot" />
                  <span className={`badge ${e.source}`}>{e.source === 'novel' ? 'NOVEL' : 'DIARY'}</span>
                </div>
                <h3>{e.title}</h3>
                <p className="preview">{e.content}</p>
                {e.tags?.length ? <Tags tags={e.tags} source={e.source} /> : null}
              </button>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <section className="overlay" onClick={() => setSelected(undefined)}>
          <article className={`sheet ${selected.source}`} onClick={e => e.stopPropagation()}>
            <header className="sheet-head">
              <div>
                <div className="meta">
                  <span className="muted">{new Date(selected.date).toLocaleDateString()}</span>
                  <span className={`badge ${selected.source}`}>{selected.source === 'novel' ? 'NOVEL' : 'DIARY'}</span>
                </div>
                <h2>{selected.title}</h2>
              </div>
              <button className="ghost" onClick={() => setSelected(undefined)}>閉じる</button>
            </header>
            <div className="content-scroll">
              <p className="content">{selected.content}</p>
            </div>
            {selected.tags?.length ? <Tags tags={selected.tags} source={selected.source} /> : null}
          </article>
        </section>
      )}
    </main>
  )
}
