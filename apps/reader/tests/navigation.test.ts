import { describe, expect, test } from 'bun:test'

import {
  PRIMARY_NAVIGATION,
  navigationItemIsActive,
} from '../lib/navigation'

describe('KafLog primary navigation', () => {
  test('defines the four memory-reading modes in canonical order', () => {
    expect(PRIMARY_NAVIGATION.map(item => item.label)).toEqual([
      'Timeline',
      'Diaries',
      'Novels',
      'People Said',
    ])
  })

  test('links only routes that currently exist', () => {
    const byKey = Object.fromEntries(
      PRIMARY_NAVIGATION.map(item => [item.key, item.href]),
    )

    expect(byKey.timeline).toBeNull()
    expect(byKey.diaries).toBe('/')
    expect(byKey.novels).toBe('/novels')
    expect(byKey['people-said']).toBe('/people-said')
  })

  test('never creates duplicate enabled hrefs', () => {
    const hrefs = PRIMARY_NAVIGATION.flatMap(item =>
      item.href === null ? [] : [item.href],
    )

    expect(new Set(hrefs).size).toBe(hrefs.length)
  })

  test('marks diary home and detail URLs as Diaries', () => {
    const diaries = PRIMARY_NAVIGATION.find(item => item.key === 'diaries')!

    expect(navigationItemIsActive(diaries, '/')).toBeTrue()
    expect(navigationItemIsActive(diaries, '/day/2026-08-13')).toBeTrue()
    expect(navigationItemIsActive(diaries, '/people-said')).toBeFalse()
  })

  test('marks Novel list and detail URLs as Novels', () => {
    const novels = PRIMARY_NAVIGATION.find(item => item.key === 'novels')!

    expect(navigationItemIsActive(novels, '/novels')).toBeTrue()
    expect(
      navigationItemIsActive(
        novels,
        '/novels/11111111-1111-4111-8111-111111111111',
      ),
    ).toBeTrue()
    expect(navigationItemIsActive(novels, '/')).toBeFalse()
  })

  test('marks People Said only on its route family', () => {
    const peopleSaid = PRIMARY_NAVIGATION.find(
      item => item.key === 'people-said',
    )!

    expect(navigationItemIsActive(peopleSaid, '/people-said')).toBeTrue()
    expect(navigationItemIsActive(peopleSaid, '/people-said/example')).toBeTrue()
    expect(navigationItemIsActive(peopleSaid, '/')).toBeFalse()
  })
})
