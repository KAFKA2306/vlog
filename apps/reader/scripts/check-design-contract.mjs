import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const cssPath = resolve(here, '../app/globals.css')
const css = readFileSync(cssPath, 'utf8')

function fail(message) {
  console.error(`design-contract: ${message}`)
  process.exitCode = 1
}

const forbidden = [
  ['legacy black canvas', '#05070a'],
  ['legacy cyan accent', '#75e6ff'],
  ['radial neon treatment', 'radial-gradient'],
  ['hover lift transform', 'translateY('],
]

for (const [name, needle] of forbidden) {
  if (css.includes(needle)) fail(`${name} is forbidden (${needle})`)
}

const requiredTokens = [
  '--color-canvas',
  '--color-paper',
  '--color-ink',
  '--color-ink-muted',
  '--color-accent',
  '--color-border',
  '--color-diary',
  '--color-novel',
  '--color-people-said',
  '--color-focus',
]

for (const token of requiredTokens) {
  if (!css.includes(`${token}:`)) fail(`missing required semantic token ${token}`)
}

if (!css.includes('outline: 3px solid var(--color-focus)')) {
  fail('author-defined focus indicator must use the canonical 3px focus outline')
}

if (!css.includes('@media (prefers-reduced-motion: reduce)')) {
  fail('prefers-reduced-motion contract is missing')
}

function tokenHex(name) {
  const match = css.match(new RegExp(`${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*:\\s*(#[0-9a-fA-F]{6})`))
  if (!match) {
    fail(`cannot read hex value for ${name}`)
    return '#000000'
  }
  return match[1]
}

function channelToLinear(value) {
  const normalized = value / 255
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4
}

function luminance(hex) {
  const value = hex.slice(1)
  const r = channelToLinear(Number.parseInt(value.slice(0, 2), 16))
  const g = channelToLinear(Number.parseInt(value.slice(2, 4), 16))
  const b = channelToLinear(Number.parseInt(value.slice(4, 6), 16))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrastRatio(foreground, background) {
  const a = luminance(foreground)
  const b = luminance(background)
  const lighter = Math.max(a, b)
  const darker = Math.min(a, b)
  return (lighter + 0.05) / (darker + 0.05)
}

const canvas = tokenHex('--color-canvas')
const paper = tokenHex('--color-paper')
const textTokens = [
  '--color-ink',
  '--color-ink-muted',
  '--color-accent',
  '--color-diary',
  '--color-novel',
  '--color-people-said',
]

for (const token of textTokens) {
  const foreground = tokenHex(token)
  for (const [surfaceName, background] of [
    ['canvas', canvas],
    ['paper', paper],
  ]) {
    const ratio = contrastRatio(foreground, background)
    if (ratio < 4.5) {
      fail(`${token} contrast on ${surfaceName} is ${ratio.toFixed(2)}:1; expected >= 4.5:1`)
    }
  }
}

if (process.exitCode) process.exit(process.exitCode)
console.log('design-contract: semantic tokens, legacy-theme ban, focus, motion, and text contrast all pass')
