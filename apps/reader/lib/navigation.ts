export type NavigationItem = {
  key: 'timeline' | 'diaries' | 'novels' | 'people-said'
  label: string
  href: string | null
  activePrefixes: readonly string[]
}

export const PRIMARY_NAVIGATION: readonly NavigationItem[] = [
  {
    key: 'timeline',
    label: 'Timeline',
    href: '/timeline',
    activePrefixes: ['/timeline'],
  },
  {
    key: 'diaries',
    label: 'Diaries',
    href: '/',
    activePrefixes: ['/', '/day/'],
  },
  {
    key: 'novels',
    label: 'Novels',
    href: '/novels',
    activePrefixes: ['/novels'],
  },
  {
    key: 'people-said',
    label: 'People Said',
    href: '/people-said',
    activePrefixes: ['/people-said'],
  },
] as const

export const navigationItemIsActive = (item: NavigationItem, pathname: string) => {
  if (item.key === 'diaries' && pathname === '/') return true
  return item.activePrefixes.some(prefix => prefix !== '/' && pathname.startsWith(prefix))
}
