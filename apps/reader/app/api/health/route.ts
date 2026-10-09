export const dynamic = 'force-dynamic'

function optionalEnv(name: string) {
  const value = process.env[name]?.trim()
  return value ? value : null
}

export async function GET() {
  return Response.json(
    {
      status: 'ok',
      gitCommitSha:
        optionalEnv('VLOG_DEPLOY_GIT_SHA') ?? optionalEnv('VERCEL_GIT_COMMIT_SHA'),
      gitCommitRef:
        optionalEnv('VLOG_DEPLOY_GIT_REF') ?? optionalEnv('VERCEL_GIT_COMMIT_REF'),
      deploymentId: optionalEnv('VERCEL_DEPLOYMENT_ID'),
      environment: optionalEnv('VERCEL_ENV'),
    },
    {
      headers: {
        'Cache-Control': 'no-store',
      },
    },
  )
}
