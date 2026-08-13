import http from 'node:http'

const imageUrl = 'http://127.0.0.1:54321/fixture-image.svg'

const diaries = [
  {
    id: 'diary-visual-1',
    date: '2026-08-13',
    title: '静かな夜の記録',
    content: 'その日の出来事を、あとから読み返せるように短くまとめた公開用のfixtureです。',
    image_url: imageUrl,
    is_public: true,
  },
  {
    id: 'diary-visual-2',
    date: '2026-08-12',
    title: '昨日から今日へ',
    content: '日付が変わっても同じ個人史として自然に続いて見えることを確認します。',
    image_url: null,
    is_public: true,
  },
]

const novels = [
  {
    id: 'novel-visual-1',
    date: '2026-08-13',
    title: '記憶から生まれた小さな物語',
    content: 'これは事実記録ではなく、記憶から派生したNarrative Artifactのvisual fixtureです。',
    image_url: imageUrl,
    is_public: true,
  },
]

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540"><rect width="960" height="540" fill="#f5f4ef"/><circle cx="480" cy="270" r="120" fill="#0f766e" opacity=".16"/><path d="M260 330 C380 190 580 190 700 330" fill="none" stroke="#0f766e" stroke-width="18" stroke-linecap="round"/><text x="480" y="430" text-anchor="middle" font-family="sans-serif" font-size="28" fill="#1a1c20">KafLog visual fixture</text></svg>`

const server = http.createServer((request, response) => {
  const url = new URL(request.url ?? '/', 'http://127.0.0.1:54321')

  if (url.pathname === '/fixture-image.svg') {
    response.writeHead(200, { 'content-type': 'image/svg+xml; charset=utf-8' })
    response.end(svg)
    return
  }

  const rows = url.pathname.endsWith('/daily_entries')
    ? diaries
    : url.pathname.endsWith('/novels')
      ? novels
      : null

  if (rows === null) {
    response.writeHead(404)
    response.end('not found')
    return
  }

  const offset = Number(url.searchParams.get('offset') ?? '0')
  const limit = Number(url.searchParams.get('limit') ?? '250')
  const page = rows.slice(offset, offset + limit)
  const end = page.length === 0 ? offset : offset + page.length - 1

  response.writeHead(200, {
    'content-type': 'application/json',
    'content-range': `${offset}-${end}/${rows.length}`,
  })
  response.end(JSON.stringify(page))
})

server.listen(54321, '127.0.0.1', () => {
  console.log('visual fixture server listening on 54321')
})
