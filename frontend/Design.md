# Design System: The Editorial Wellness Framework

## 1. Overview & Creative North Star
**Creative North Star: "The Mindful Curator"**

This design system moves beyond the utility of a standard tracker to become a premium digital companion. We reject the "spreadsheet" aesthetic of traditional fitness apps in favor of an **Editorial Wellness** approach. The goal is to make nutrition feel like a high-end lifestyle choice rather than a chore.

We break the "template" look through:
*   **Intentional Asymmetry:** Utilizing unbalanced whitespace to guide the eye and create a sense of bespoke craftsmanship.
*   **Tonal Depth:** Replacing harsh grid lines with a sophisticated "Layered Paper" philosophy.
*   **High-Contrast Scale:** Pairing oversized, elegant display type with functional, utilitarian body text to establish clear authority and calm.

---

## 2. Colors & Surface Philosophy

The palette is rooted in organic stability. We use deep greens to represent vitality and warm ambers to signal motivation and energy.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1x solid borders to section content. Boundaries must be defined solely through background color shifts or tonal transitions. To separate the header from a list, use a transition from `surface` to `surface-container-low`.

### Surface Hierarchy & Nesting
Treat the UI as physical layers of fine stationery.
*   **Base:** `surface` (#f9faf7) serves as the canvas.
*   **Lowered Sections:** Use `surface-container-low` (#f3f4f1) for secondary content areas like "Yesterday's Recaps."
*   **Elevated Elements:** Use `surface-container-lowest` (#ffffff) for primary cards to create a natural, soft "pop" against the background without relying on heavy shadows.

### The "Glass & Gradient" Rule
To inject "soul" into the digital interface:
*   **Signature Gradients:** Use a subtle linear gradient on primary CTAs and hero headers, transitioning from `primary` (#006036) to `primary_container` (#1a7a4a) at a 135-degree angle.
*   **Glassmorphism:** For floating navigation bars or overlays, use `surface` at 80% opacity with a `24px` backdrop-blur. This ensures the vibrant food photography "bleeds" through the UI, making it feel integrated.

---

## 3. Typography: The Editorial Voice

We pair **Manrope** (Display/Headline) for its modern, architectural feel with **Inter** (Body/Label) for its peerless legibility.

| Level | Token | Font | Size | Weight | Intent |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display** | `display-lg` | Manrope | 3.5rem | 700 | Large, motivating metrics (e.g., Calorie totals). |
| **Headline** | `headline-md` | Manrope | 1.75rem | 600 | Editorial section starts; "Your Morning Routine." |
| **Title** | `title-lg` | Inter | 1.375rem | 600 | High-level card titles and modal headers. |
| **Body** | `body-lg` | Inter | 1rem | 400 | Primary reading experience; nutritional advice. |
| **Label** | `label-md` | Inter | 0.75rem | 500 | Data points, timestamps, and micro-copy. |

---

## 4. Elevation & Depth

We achieve hierarchy through **Tonal Layering** rather than structural geometry.

*   **The Layering Principle:** Depth is "stacked." A `surface-container-highest` card should never sit directly on a `surface` background; it needs an intermediate `surface-container` step to feel natural.
*   **Ambient Shadows:** For floating elements (like an AI Coach FAB), use a "Diffusion Shadow": `0 12px 32px rgba(25, 28, 27, 0.04)`. The shadow color must be a tinted version of `on-surface`, never pure black.
*   **The Ghost Border Fallback:** If a container requires definition against a complex image, use a `1px` stroke of `outline-variant` (#bec9be) at **15% opacity**.

---

## 5. Components

### Buttons
*   **Primary:** Pill-style (`rounded-full`), 48px height. Uses the Signature Gradient (`primary` to `primary_container`). Text: `on_primary`.
*   **Secondary:** `rounded-md` (1.5rem), 48px height. Background: `secondary_fixed`. Text: `on_secondary_fixed`.
*   **Tertiary:** Ghost style. No container, `primary` text weight 600, with an iconic trailing arrow.

### Cards & Lists
*   **Zero Dividers:** Forbid the use of horizontal rules. Use a `24px` vertical gap from the Spacing Scale or a subtle shift to `surface_container_low` for the list item background on hover.
*   **Roundedness:** Standard cards use `md` (1.5rem/24px). Feature hero cards use `lg` (2rem/32px).

### AI Coach "Pulse" (Custom Component)
A floating glass container (`surface` @ 70% + blur) with a subtle `primary` glow. This houses the AI food insights, using `headline-sm` for the coaching prompts.

### Inputs & Fields
*   **Style:** Minimalist. No bottom line or box. Use a `surface-container-high` background with `sm` (0.5rem) rounded corners.
*   **Focus State:** A soft `2px` glow of `primary` at 20% opacity, rather than a harsh border change.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use extreme whitespace (e.g., 64px+) to separate major editorial sections.
*   **Do** use "Warm Amber" (`secondary`) sparingly—only for moments of achievement or critical calls to action (e.g., "Upgrade to Pro" or "Goal Reached").
*   **Do** utilize the `surface_container` tiers to create a sense of "nested" information architecture.

### Don't
*   **Don't** use 100% black (#000000). Always use `on_surface` (#191c1b) for text to maintain a premium, soft-contrast look.
*   **Don't** use standard "drop shadows" with 20%+ opacity. They look cheap and dated.
*   **Don't** use square corners. Every element must feel organic and "held," utilizing the defined Roundedness Scale.
*   **Don't** use icons without purpose. Icons should be `filled` when active and `outline` when inactive to minimize visual noise.