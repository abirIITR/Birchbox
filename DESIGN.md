---
name: The Beauty of Makeup
description: Haute editorial beauty presentation system pairing monumental extended grotesque headlines (Syne) with porcelain tones and coral accents
colors:
  primary: "#DE4B52"
  primary-deep: "#B63454"
  accent-rose: "#DB97A4"
  accent-blush: "#F8B2BF"
  neutral-bg: "#F9EFEB"
  neutral-surface: "#FFFFFF"
  neutral-text: "#575953"
  neutral-black: "#000000"
typography:
  display:
    fontFamily: "Extenda-30Deca, 'Monument Extended', sans-serif"
    fontSize: "clamp(48px, 9vw, 96px)"
    fontWeight: 900
    lineHeight: 0.88
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Extenda-30Deca, 'Monument Extended', sans-serif"
    fontSize: "clamp(32px, 5vw, 64px)"
    fontWeight: 900
    lineHeight: 0.95
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Aileron, 'Plus Jakarta Sans', Inter, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: "Aileron, 'Plus Jakarta Sans', Inter, sans-serif"
    fontSize: "14px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.08em"
  numerals:
    fontFamily: "Etna, Cinzel, serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.05em"
rounded:
  none: "0px"
  sm: "2px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
  canvas: "81px"
components:
  card-editorial:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.neutral-text}"
    rounded: "{rounded.none}"
    padding: "0px"
  tag-meta:
    backgroundColor: "transparent"
    textColor: "{colors.neutral-text}"
    rounded: "{rounded.none}"
    padding: "4px 0px"
---

# Design System: The Beauty of Makeup

## Overview

**Creative North Star: "The Architectural Monograph: Pure Chromatic Grotesque"**

The visual world of *The Beauty of Makeup* embodies the bold, uncompromising authority of Swiss modernist editorial design. Based on `BeautyTemplate.pdf`, the system centers on monumental, ultra-extended grotesque display typography (**Extenda-30Deca**) in saturated coral-crimson (`#DE4B52`), grounded by a luminous porcelain ivory canvas (`#F9EFEB`) and restrained editorial charcoal copy (`#575953`).

Per explicit creative direction, the visual language rejects decorative cursive and script typefaces in favor of pure, confident, architectural typography. Visual interest comes from bold scale contrast—massive extended all-caps titles juxtaposed with delicate running tags and razor-sharp rectangular image frames. It eschews generic soft shadows, gradient fills, and rounded cards in favor of stark planar hierarchy and disciplined asymmetrical negative space.

**Key Characteristics:**
- **Monumental Extended Typography:** Ultra-wide all-caps headers (**Extenda-30Deca**) anchor each view with raw editorial power.
- **Pure Grotesque Restraint:** Zero cursive or handwritten script fonts; every title and label speaks with clean, architectural precision.
- **Luminous Porcelain Foundation:** Soft warm ivory (`#F9EFEB`) replaces clinical white, providing archival warmth and harmonizing with cosmetics and skin tones.
- **Zero-Radius Framing:** Strict `0px` borders and razor-sharp photographic grids create an unyielding editorial magazine layout.
- **Persistent Meta Anchors:** Consistent header/footer coordinates maintain continuity across all views and layouts.

---

## Colors

The color palette is derived directly from cosmetic pigments—coral reds, crushed berry roses, warm porcelain foundation, and carbon eyeliner:

### Primary
- **Poppy Crimson / Coral Red** (`#DE4B52` / `rgb(222, 75, 82)`): The dominant brand voice. Used exclusively for monumental headlines, active range highlights, and key metric readouts.
- **Deep Crimson / Raspberry Rose** (`#B63454` / `rgb(182, 52, 84)`): Supporting saturated shadow tone for vector backgrounds, deep graphic accents, and active button hovers.

### Secondary & Accents
- **Dusty Rose / Blush Mauve** (`#DB97A4` / `rgb(219, 151, 164)`): Used for numbering (`01`, `02`, ..., `15`), subtitle highlight pills, and subdued editorial indicators.
- **Baby Blush Pink** (`#F8B2BF` / `rgb(248, 178, 191)`): Subtle border tints, tag outlines, and delicate accents.

### Neutral
- **Porcelain Ivory Canvas** (`#F9EFEB` / `rgb(249, 239, 235)`): The primary background across all surfaces. Warm, organic, and archival.
- **Editorial Olive-Charcoal** (`#575953` / `rgb(87, 89, 83)`): The primary body copy and metadata text color. Replaces harsh `#000000` for long-form narrative, providing a 6.8:1 WCAG AAA contrast ratio.
- **Deep Obsidian Black** (`#232521`): Reserved strictly for high-contrast masthead headers and focal boundaries.
- **Crisp Pure White** (`#FFFFFF`): Used for museum mat card backgrounds, crisp image borders, and clean negative cutouts.

### Named Rules
- **The Porcelain Canvas Rule:** Never use pure clinical `#FFFFFF` as the full-viewport canvas background. Surfaces must always rest on `#F9EFEB` to preserve warm skin-tone harmony.
- **The Red Rarity Rule:** The primary red (`#DE4B52`) is reserved exclusively for major headlines, metrics, and active slider highlights. It must never be applied to body paragraphs or continuous narrative text.
- **The Non-Cursive Rule:** All typography remains strictly grotesque, neo-grotesque, or classical serif numerals. No cursive, handwritten, or brush scripts are permitted.

---

## Typography

**Display & Headline Font:** `Syne` (matching `Extenda-30Deca`, fallback: `Monument Extended`, `Arial Black` with `letter-spacing: -0.02em`)
**Numeral / Index Font:** `Etna-Regular` / `Cinzel` (Fallback: `Cormorant Garamond`, `Bodoni MT`)
**Body & Metadata Font:** `Aileron-Regular` / `Plus Jakarta Sans` / `Inter` (Fallback: `Helvetica Neue`, `Avenir`)

### Hierarchy Specification

| Text Role | Font Family | Weight | Size (PDF pt / CSS rem) | Line Height | Letter Spacing | Case & Transform |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hero Cover Title** | Extenda (30 Deca) | 900 | 472.3pt / `clamp(5rem, 15vw, 14rem)` | 0.85 | `+0.04em` | UPPERCASE |
| **Slide Header** | Extenda (30 Deca) | 900 | 204.8pt / `clamp(2.5rem, 6.5vw, 6rem)` | 0.88 | `+0.02em` | UPPERCASE |
| **Section Eyebrow Tag** | Extenda (30 Deca) | 800 | 11.0pt / `0.75rem` | 1.00 | `+0.12em` | UPPERCASE |
| **Slide Number** | Etna / Cinzel | 700 | 30.5pt / `1.4rem` | 1.00 | `+0.05em` | Tabular Numerals |
| **Running Metadata** | Plus Jakarta Sans | 700 | 21.0pt / `0.95rem` | 1.20 | `+0.08em` | Title Case |
| **Body Narrative** | Plus Jakarta Sans | 400 | 24.0pt / `1.15rem` | 1.55 | `normal` | Sentence case (max 48ch) |

---

## Layout

All layouts are constructed on a strict **16:9 widescreen presentation canvas** (`1440px × 810px` base coordinates, scalable via viewport units).

### Spatial Grid & Coordinates
- **Outer Canvas Margins:** `81px` (5.625% of width) inset on top, bottom, and left edges.
- **Top-Left Persistent Brand Tag:** Fixed at `x = 81.0px`, `y = 46.6px` (`Liceria & Co. // @reallygreatsite`).
- **Bottom-Left Presenter Attribution:** Fixed at `x = 81.0px`, `y = 723.6px` (`Presented by Juliana Silva`).
- **Bottom-Right Slide Index:** Fixed at `x = 1261.4px`, `y = 717.8px` (`[01-15] // Slide`).

---

## Elevation & Depth

**Depth Philosophy: Planar & Sharp Stacking (Zero Modern Soft Shadows)**

This design system avoids blurry modern CSS box-shadows (`box-shadow: 0 10px 30px rgba(0,0,0,0.1)`). Instead, depth and visual hierarchy are generated through:
1. **Layered Card Planar Stacking:** High-contrast solid white containers (`#FFFFFF`) layered directly over the warm porcelain canvas (`#F9EFEB`), creating physical paper-mat depth.
2. **Hairline Precision Borders:** Refined `1px solid #E8DDD7` borders providing crisp spatial boundaries.

### Named Rules
- **The Zero-Blur Elevation Rule:** No blurred drop shadows are permitted on any surface, card, or text element. All depth must be planar and sharp.

---

## Shapes

- **Corner Radius:** Strictly `0px` (`rounded.none`). All cards, photo frames, buttons, sliders, and visual containers maintain sharp, razor-cut $90^\circ$ editorial corners.
- **Aspect Ratios:** Photographic assets conform strictly to standard editorial ratios:
  - `1:1` Square (Product detail crops)
  - `4:5` / `3:4` Vertical Portrait (Model looks, skincare portraits)
  - `16:9` / `2.35:1` Panoramic Landscape (Horizontal banners and multi-product sets)
- **Image Mats:** Photos are framed with crisp `0px` to `8px` white mat margins (`#FFFFFF`) to emulate museum print mounting.

---

## Components

### 1. Slide Canvas & Persistent Metadata Frame
Every slide is bounded by a persistent running metadata frame:
- **Top-Left Header:** `Liceria & Co. // @reallygreatsite` (Plus Jakarta Sans Bold, `#575953`)
- **Bottom-Left Footer:** `Presented by Juliana Silva` (Plus Jakarta Sans Bold, `#575953`)
- **Bottom-Right Slide Index:** `01 Slide` (Cinzel Bold `#DB97A4` + Plus Jakarta Sans Bold `#575953`)

### 2. Monumental Headline Block
- **Element:** All-caps header in `Syne` (weight 900).
- **Styling:** Line-height `0.88`, color `#DE4B52`, letter-spacing `+0.04em`.
- **Usage:** Positioned aggressively at slide margins to command visual focus.

### 3. Photographic Editorial Container
- **Element:** Razor-sharp rectangular image frame.
- **Styling:** Solid mat backing, `border-radius: 0px`, overflow hidden, object-fit cover.

### 4. 3-Column Diagnostic Card Stack
- **Element:** 3 parallel vertical text containers for categorized content.
- **Header:** Extended Extenda bold heading.
- **Body:** Clean narrative paragraph (`Plus Jakarta Sans`, 24pt, `#575953`).

---

## Do's and Don'ts

### Do:
- **DO** embrace extreme scale tension: let headlines be colossal (`clamp(3rem, 7vw, 7rem)`) in bold `Syne` while body copy remains delicately sized (`16px`/`24pt`).
- **DO** keep the canvas background warm porcelain (`#F9EFEB`), never clinical `#FFFFFF`.
- **DO** maintain razor-sharp `0px` border-radii across all images, containers, and borders.
- **DO** keep the running metadata anchors (`Liceria & Co.`, presenter attribution, slide number) in their exact coordinate positions across all slides.

### Don't:
- **DON'T** use cursive, calligraphic, or handwritten script fonts anywhere in the system.
- **DON'T** introduce modern UI tropes such as rounded corners (`border-radius: 8px/12px`), glassmorphism, or blurred CSS shadows (`box-shadow: 0 4px 20px rgba(...)`).
- **DON'T** use gradient fills on text or backgrounds; color transitions must be solid and deliberate.
- **DON'T** color body text with primary red (`#DE4B52`); red is reserved strictly for high-impact headings and active metrics.
- **DON'T** let body text columns stretch beyond 48 characters wide; wrap into multi-column editorial blocks instead.
