import { afterEach, describe, expect, it } from 'vitest'

import { GET } from '../app/api/health/route'

const ENV_KEYS = [
  'VERCEL_GIT_COMMIT_SHA',
  'VERCEL_GIT_COMMIT_REF',
  'VERCEL_DEPLOYMENT_ID',
  'VERCEL_ENV',
] as const

const originalEnvironment = Object.fromEntries(
  ENV_KEYS.map(key => [key, process.env[key]]),
)

afterEach(() => {
  for (const key of ENV_KEYS) {
    const originalValue = originalEnvironment[key]
    if (originalValue === undefined) {
      delete process.env[key]
    } else {
      process.env[key] = originalValue
    }
  }
})

describe('GET /api/health', () => {
  it('returns Vercel deployment identity without caching', async () => {
    process.env.VERCEL_GIT_COMMIT_SHA = '0123456789abcdef'
    process.env.VERCEL_GIT_COMMIT_REF = 'main'
    process.env.VERCEL_DEPLOYMENT_ID = 'dpl_example'
    process.env.VERCEL_ENV = 'production'

    const response = await GET()
    const payload = await response.json()

    expect(response.status).toBe(200)
    expect(response.headers.get('cache-control')).toBe('no-store')
    expect(payload).toEqual({
      status: 'ok',
      gitCommitSha: '0123456789abcdef',
      gitCommitRef: 'main',
      deploymentId: 'dpl_example',
      environment: 'production',
    })
  })

  it('returns null deployment metadata outside Vercel', async () => {
    for (const key of ENV_KEYS) delete process.env[key]

    const response = await GET()
    const payload = await response.json()

    expect(payload).toEqual({
      status: 'ok',
      gitCommitSha: null,
      gitCommitRef: null,
      deploymentId: null,
      environment: null,
    })
  })
})
