# Vlog Serendie Design System

Welcome to the **Vlog Serendie Design System**. This design language is crafted to provide a premium, accessible, and innovative digital experience for the Vlog platform. It draws inspiration from the **Digital Agency Japan (Digital Cho)** for its commitment to accessibility and systematic structure, and **Mitsubishi Serendie** for its focus on adaptive, borderless digital innovation and co-creation.

## 1. Philosophy: "Human-Centric Digital Innovation"
Our design philosophy merges structured utility with aspirational aesthetics.
- **Accessibility First (from Digital Cho):** Information must be accessible to everyone. High contrast, clear typography, and semantic structure are non-negotiable foundations.
- **Borderless & Adaptive (from Serendie):** The interface adapts seamlessly across devices and contexts, breaking down barriers between users and content.
- **Premium Simplicity:** We prioritize clarity and elegance. Use "Glassmorphism" and subtle motion to create depth and delight without clutter.

## 2. Core Visual Language

### 2.1 Colors (HSL)
We use a vibrant HSL palette for maximum flexibility and modern aesthetic appeal.

**Primary Brand Colors:**
- **Digital Blue:** `hsl(210, 100%, 36%)` (#005CB9 - Trust, Navigation)
- **Serendie Teal:** `hsl(184, 100%, 34%)` (#00A3AF - Innovation, Accent)
- **Vibrant Accent:** `hsl(330, 85%, 60%)` (Energy, Highlights)

**Neutral & Surface Colors:**
- **Background (Dark):** `hsl(220, 20%, 10%)`
- **Surface (Glass):** `hsla(220, 20%, 20%, 0.6)` (with backdrop-filter: blur(12px))
- **Text Primary:** `hsl(220, 10%, 95%)`
- **Text Secondary:** `hsl(220, 10%, 70%)`

### 2.2 Typography
We use a modern, geometric sans-serif stack for UI and a reliable sans-serif for content.
- **English UI:** `Inter`, `Outfit`, or system-ui.
- **Japanese Content:** `Noto Sans JP`, `Hiragino Kaku Gothic ProN`, sans-serif.
- **Code:** `Fira Code`, `Source Code Pro`, monospace.

**Scale:**
- **Display:** 3rem (48px) - Bold
- **Heading 1:** 2rem (32px) - Bold
- **Heading 2:** 1.5rem (24px) - SemiBold
- **Body:** 1rem (16px) - Regular
- **Small:** 0.875rem (14px) - Regular

### 2.3 Spacing & Layout
Based on an **8px grid system**.
- **Small:** 4px, 8px
- **Medium:** 16px, 24px
- **Large:** 32px, 48px, 64px
- **Container Max-Width:** 1200px (centered)

### 2.4 Effects & Depth
- **Glassmorphism:** Used for cards, navigational elements, and overlays.
  - `background: hsla(220, 20%, 20%, 0.4);`
  - `backdrop-filter: blur(12px);`
  - `border: 1px solid hsla(220, 10%, 90%, 0.1);`
- **Shadows:** Soft, diffused colored shadows to create "glow" rather than just depth.
  - `box-shadow: 0 4px 20px hsla(220, 90%, 56%, 0.2);`

## 3. UI Components

### 3.1 Buttons
- **Primary:** Gradient background (Blue -> Purple), text white, soft glow on hover.
- **Secondary:** Glassmorphic background, border accent, text white.
- **Ghost:** Transparent background, text accent, hover background heavy-glass.

### 3.2 Cards
- **Standard:** Glassmorphic surface, 12px rounded corners, subtle border.
- **Interactive:** Scale up (1.02) on hover, increase glow opacity.

### 3.3 Inputs
- **Field:** Darker glass background (`hsla(220, 20%, 10%, 0.6)`), light border on focus (`Serendie Blue`).
- **Label:** Floating or top-aligned, secondary text color.

### 3.4 Navigation
- **Bar:** Sticky top, heavy glass effect (`backdrop-filter: blur(20px)`), bottom border linear gradient.

## 4. Implementation Guidelines (CSS Variables)
Define these in your `:root` or `html` block.

```css
:root {
  /* Colors */
  --color-primary: 220, 90%, 56%;
  --color-accent: 330, 85%, 60%;
  --color-surface: 220, 20%, 20%;
  --color-background: 220, 20%, 10%;
  
  /* Typography */
  --font-sans: 'Inter', 'Noto Sans JP', sans-serif;
  
  /* Effects */
  --glass-bg: hsla(var(--color-surface), 0.6);
  --glass-border: 1px solid hsla(0, 0%, 100%, 0.1);
  --glass-blur: blur(12px);
}
```

## 5. Accessibility Checklist (Digital Cho Standard)
- [ ] Contrast ratio at least 4.5:1 for normal text.
- [ ] Focus states are clearly visible (outline/glow).
- [ ] Semantic HTML tags (`<nav>`, `<main>`, `<article>`, `<button>`).
- [ ] `aria-labels` for icon-only buttons.
