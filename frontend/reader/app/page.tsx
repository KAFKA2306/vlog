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
  image_url?: string | null
}

const Tags = ({ tags }: { tags: string[] }) => (
  <div className="tags">
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
          .select('id,date,title,content,tags,image_url')
          .eq('is_public', true)
          .order('date', { ascending: false })
          .limit(60)
      ])

      if (summariesResult.error) throw summariesResult.error
      if (novelsResult.error) throw novelsResult.error

      const summaries = (summariesResult.data || []).map(e => {
        const dateStr = e.date.substring(0, 10).replace(/-/g, '')
        return {
          ...e,
          source: 'summary',
          image_url: `/infographics/${dateStr}_summary.png`
        } as Entry
      })
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
          <h1>VRChat Auto Diary</h1>
          <p>Immersive memories from the virtual world.</p>
        </header>

        <div className="controls">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search memories..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="search-input"
            />
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
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="entry" style={{ height: '320px', opacity: 0.5 }}></div>
            ))}
          </div>
        )}

        {error && (
          <div className="empty-state">
            <p>❌ {error}</p>
            <button className="ghost" onClick={fetchEntries}>Retry</button>
          </div>
        )}

        {!loading && !error && filteredEntries.length === 0 && (
          <div className="empty-state">
            <p>No entries found.</p>
          </div>
        )}

        {!loading && !error && filteredEntries.length > 0 && (
          <div className="list">
            {filteredEntries.map(e => (
              <div key={e.id} className={`entry ${e.source}`} onClick={() => setSelected(e)}>
                {e.image_url && (
                  <div
                    className="entry-bg"
                    style={{ backgroundImage: `url(${e.image_url})` }}
                  />
                )}
                <div className="entry-overlay" />
                <div className="entry-content">
                  <div className="meta">
                    <span>{new Date(e.date).toLocaleDateString()}</span>
                    <span className={`badge ${e.source}`}>{e.source === 'novel' ? 'NOVEL' : 'DIARY'}</span>
                  </div>
                  <h3>{e.title}</h3>
                  <p className="preview">{e.content}</p>
                  {e.tags?.length ? <Tags tags={e.tags} /> : null}
                </div>
              </div>
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
                  <span>{new Date(selected.date).toLocaleDateString()}</span>
                  <span className={`badge ${selected.source}`}>{selected.source === 'novel' ? 'NOVEL' : 'DIARY'}</span>
                </div>
                <h2>{selected.title}</h2>
              </div>
              <button className="ghost" onClick={() => setSelected(undefined)}>Close</button>
            </header>
            <div className="sheet-content-scroll">
              {selected.image_url && (
                <img src={selected.image_url} alt={selected.title} className="sheet-image" />
              )}
              <p style={{ whiteSpace: 'pre-wrap' }}>{selected.content}</p>
              {selected.tags?.length ? <Tags tags={selected.tags} /> : null}
            </div>
          </article>
        </section>
      )}
    </main>
  )
}
