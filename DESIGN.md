---
name: Hamro Baari Organic Earth
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#3f493f'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#6f7a6e'
  outline-variant: '#becabc'
  surface-tint: '#006d30'
  primary: '#00652c'
  on-primary: '#ffffff'
  primary-container: '#15803d'
  on-primary-container: '#d3ffd5'
  inverse-primary: '#79db8d'
  secondary: '#904d00'
  on-secondary: '#ffffff'
  secondary-container: '#fe932c'
  on-secondary-container: '#663500'
  tertiary: '#9a3500'
  on-tertiary: '#ffffff'
  tertiary-container: '#c34500'
  on-tertiary-container: '#fff0ec'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#95f8a7'
  primary-fixed-dim: '#79db8d'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#005323'
  secondary-fixed: '#ffdcc3'
  secondary-fixed-dim: '#ffb77d'
  on-secondary-fixed: '#2f1500'
  on-secondary-fixed-variant: '#6e3900'
  tertiary-fixed: '#ffdbce'
  tertiary-fixed-dim: '#ffb599'
  on-tertiary-fixed: '#370e00'
  on-tertiary-fixed-variant: '#7f2b00'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Noto Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 52px
  display-lg-mobile:
    fontFamily: Noto Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg:
    fontFamily: Noto Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 42px
  headline-lg-mobile:
    fontFamily: Noto Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 34px
  headline-md:
    fontFamily: Noto Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Noto Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Noto Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Noto Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-sm:
    fontFamily: Noto Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  label-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-tablet: 1.5rem
  gutter-desktop: 2rem
  margin: 1rem
  margin-tablet: 2rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system establishes an agricultural, deeply rooted, and community-first aesthetic crafted for fresh produce distribution. It unites the organic vitality of Himalayan valley agriculture with contemporary digital ergonomics. The emotional tone evokes the trust of a neighborhood farmers' market, the crisp freshness of early morning harvests, and unshakeable logistical clarity.

Targeting multi-generational households, local urban consumers, and local farming cooperatives across Nepal, the UI balances accessibility with modern craft. The visual movement is **Organic Modernism**: generous cream surfaces, rich forest undertones, sun-ripened terracotta focal points, generous touch surfaces, and tactile cards that feel warm, honest, and grounded rather than cold or hyper-digitized.

## Colors
The palette derives from agricultural cycles: fertile soil, dense foliage, clay pots, and morning light. 

- **Primary (`#15803D`, Deep Emerald Forest)**: Represents freshness, verified organic integrity, and key interaction pathways. Tonal variations reach deep evergreen (`#166534`) for high-contrast accessibility on body text accents and borders.
- **Secondary (`#D97706`, Sunlit Amber)**: Drives dynamic actions, pending fulfillment indicators, and secondary highlights.
- **Tertiary (`#EA580C`, Terracotta Soil)**: Reserved for urgent operational notices, discount markers, immediate harvest callouts, and seasonal alerts.
- **Surface & Canvas Tones**: Clean cream foundations (`#FDFBF7` canvas, `#F7F4EC` container fill, `#FFFFFF` card surfaces) replace sterile digital grays, providing warmth and reducing visual fatigue in outdoor daylight.
- **Neutrals (`#1E293B` to `#334155`)**: Slate-rich charcoal neutrals maintain AA/AAA contrast ratios against cream backdrops, avoiding pure stark blacks.

## Typography
Typography is architected around bilingual clarity (Devanagari script alongside Latin English). **Noto Sans** is designated across headlines and structural copy to provide native conjunct support, proportional vowel marker vertical space, and consistent typographic color between Nepali and English scripts. **Inter** handles technical labels, pricing, dates, telemetry, and compact status badging.

Due to vowel matras and upper/lower conjuncts in Devanagari script, line-height multipliers are calibrated slightly looser (1.4x to 1.6x) than typical Latin-only interfaces to prevent glyph clipping. When bilingual stacked titles appear (Nepali primary with English secondary), the secondary Latin line is formatted at 75% scale in medium weight using label styling.

## Layout & Spacing
The layout follows a fluid-responsive grid system designed around one-handed mobile utility, progressing into structured multi-column displays for larger displays:

- **Mobile (<640px)**: 4-column layout, 16px margins, 16px gutters. Primary actions and navigation triggers occupy a persistent bottom thumb zone (minimum 48px touch height).
- **Tablet (640px–1024px)**: 8-column layout, 32px margins, 24px gutters. Product listings transition from single-column vertical cards to an alternating 2-column or 3-column catalog grid.
- **Desktop (>1024px)**: 12-column layout, max-width 1280px centered container, 48px outer margins, 32px gutters.

Rhythmic vertical spacing relies strictly on multiples of 4px and 8px, using `space-sm` for related label-to-input groupings, `space-md` for standard component internals, and `space-xl` between logical page sections.

## Elevation & Depth
Depth is created through warm, natural layering rather than cold synthetic drop shadows:

- **Surface Layering**: The primary viewport sits on an organic cream base (`#FDFBF7`). Secondary groupings use soft-fill containers (`#F7F4EC`). Cards and actionable modal surfaces sit on crisp pure white (`#FFFFFF`) to naturally lift content.
- **Ambient Earth Shadows**: Shadows utilize a warm neutral tint derived from the slate-soil palette (`rgba(30, 41, 59, 0.06)` and `rgba(30, 41, 59, 0.12)`) with broad diffusion radii (16px to 24px blur). This replicates natural daylight over farm fields rather than artificial dark gray drop shadows.
- **Borders as Subtle Grounding**: In addition to diffuse shadows, elevated interactive elements feature a hairline border (`1px solid rgba(21, 128, 61, 0.08)`) to maintain physical legibility under direct sunlight.

## Shapes
The visual geometry reflects natural organic curves with structural restraint. 
- Core interactive cards, modals, and container wrappers adopt a generous `rounded-2xl` profile (16px / 1rem radius), projecting friendliness and approachability.
- Action tags, produce classification chips, and primary buttons use full pill radiuses (`rounded-full`) to offer inviting, tactile touch targets.
- Form controls and inputs maintain `rounded-xl` (12px / 0.75rem) to ensure geometric stability alongside bilingual typography.

## Components

### Buttons
- **Primary Action**: Forest Green (`#15803D`) background with white typography, min-height 52px for mobile ergonomics, pill-shaped (`rounded-full`), with subtle ambient hover translation (`translate-y-[-1px]`).
- **Secondary Action**: Bordered terracotta or amber (`1.5px solid #D97706`) with tinted background fill (`rgba(217, 119, 6, 0.06)`).
- **Cart/Checkout Controls**: Sticky full-width mobile container with bilingual breakdown (e.g., "अर्डर गर्नुहोस् / Place Order") displaying item count and localized Nepalese Rupee (`रु / NPR`) totals.

### Produce Cards
- Composed on pure white (`#FFFFFF`) with a 16px border radius, subtle warm shadow, and a 1px soft cream/forest border.
- Cards host an agricultural origin badge (e.g., "काभ्रे / Kavre Direct"), unit weight, bilingual title, harvest timestamp, and an oversized '+' increment stepper directly accessible via the thumb zone.

### Chips & Badges
- **Organic/Origin Badges**: Pill-shaped with soft natural fills (`#DCFCE7` green tint with `#166534` text) and delicate leaf iconography.
- **Harvest Freshness Tag**: Amber pill badge (`#FEF3C7` with `#92400E` text) denoting hours elapsed since harvest.

### Form Inputs & Voice Search
- Text inputs provide 48px height minimum, padded with 16px horizontal clearance, framed with a 1.5px border (`#E2E8F0`), transitioning to forest green on focus.
- **Voice Waveform Search**: Integrated microphone toggle for non-literate or rapid Nepali voice searching; active states trigger animated warm-amber waveform bars with real-time feedback.

### Status Stepper
- Step-by-step dispatch chain: *Harvested (बारीबाट संकलन) -> Cleaned & Sorted (सफाई र ग्रेडिङ) -> In Transit (बाटोमा) -> Delivered (घर पुग्यो)*.
- Connected via a 3px organic green line with circular milestone nodes containing contextual agricultural micro-icons.