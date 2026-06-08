---
name: Velocity Kinetic
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c4c9ac'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8e9379'
  outline-variant: '#444933'
  surface-tint: '#abd600'
  primary: '#ffffff'
  on-primary: '#283500'
  primary-container: '#c3f400'
  on-primary-container: '#556d00'
  inverse-primary: '#506600'
  secondary: '#ffb59a'
  on-secondary: '#5a1b00'
  secondary-container: '#ff5e07'
  on-secondary-container: '#531900'
  tertiary: '#ffffff'
  on-tertiary: '#00363a'
  tertiary-container: '#7df4ff'
  on-tertiary-container: '#006f77'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c3f400'
  primary-fixed-dim: '#abd600'
  on-primary-fixed: '#161e00'
  on-primary-fixed-variant: '#3c4d00'
  secondary-fixed: '#ffdbce'
  secondary-fixed-dim: '#ffb59a'
  on-secondary-fixed: '#370e00'
  on-secondary-fixed-variant: '#802a00'
  tertiary-fixed: '#7df4ff'
  tertiary-fixed-dim: '#00dbe9'
  on-tertiary-fixed: '#002022'
  on-tertiary-fixed-variant: '#004f54'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-xl:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  body-lg:
    fontFamily: Lexend
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.5'
  body-md:
    fontFamily: Lexend
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Lexend
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.0'
    letterSpacing: 0.1em
  metric-huge:
    fontFamily: Space Grotesk
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.0'
    letterSpacing: -0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 16px
  margin: 20px
---

## Brand & Style

This design system is engineered for elite performance, catering to athletes and data-driven fitness enthusiasts who demand precision and speed. The brand personality is aggressive, technical, and motivating, evoking the feeling of a high-end garage or a professional sports lab. 

The visual style is a fusion of **High-Contrast / Bold** aesthetics and **Minimalism**. It prioritizes immediate legibility and "glanceable" metrics. By utilizing a deep, obsidian dark mode, we create a high-performance environment where vibrant action colors "pop" to guide the user's eye toward critical performance data and primary actions. The interface should feel like a precision instrument: sharp, responsive, and devoid of unnecessary decoration.

## Colors

The palette is optimized for high-intensity environments, ensuring visibility under varied lighting conditions.

- **Primary (Electric Lime):** Reserved for the most critical "Start" actions, progress indicators, and peak performance metrics.
- **Secondary (Ignite Orange):** Used for warnings, heart-rate zones, and secondary calls to action that require urgency.
- **Tertiary (Cyber Blue):** Dedicated to technical data visualization, such as joint angles, skeletal tracking, and historical trend lines.
- **Surface Palette:** The background uses a pure black (#000000) for OLED efficiency, with varying shades of "Neutral" (#121212, #1E1E1E) to define container hierarchy.
- **Feedback:** Success uses the primary lime; Error uses a high-saturation red (#FF3B30).

## Typography

This design system employs a dual-font strategy to balance technical aggression with athletic readability.

- **Space Grotesk** is used for headlines and hero metrics. Its geometric and slightly eccentric apertures reflect a futuristic, technical aesthetic.
- **Lexend** is used for all body copy and UI labels. Designed specifically for readability, its hyper-clear character definition ensures athletes can read instructions or data while in motion.
- **Emphasis:** Critical metrics (like BPM or Velocity) should use the `metric-huge` token to dominate the visual hierarchy.

## Layout & Spacing

The system utilizes a **12-column fluid grid** for tablet/web and a **4-column fluid grid** for mobile. 

The layout philosophy emphasizes "Information Density without Clutter." Content is grouped into logical modules using cards. Vertical rhythm follows an 8px square grid, though a 4px "half-step" is permitted for tight technical readouts. Large margins (20px+) on the screen edges prevent accidental touches during physical activity and ensure content remains clear of device bezels.

## Elevation & Depth

To maintain a focused, high-performance feel, the system avoids traditional soft shadows. Depth is achieved through **Tonal Layers** and **Low-Contrast Outlines**.

- **Level 0 (Background):** Pure black (#000000).
- **Level 1 (Cards/Surface):** Dark charcoal (#121212).
- **Level 2 (In-Card Elements):** Lighter charcoal (#1E1E1E).
- **Interactive States:** Use 1px solid borders in the Primary or Secondary colors to indicate focus or active states. 
- **Data Visualization:** Use "glow" effects (0px blur, primary color) sparingly on line charts and key data points to simulate a digital cockpit or HUD (Heads-Up Display) feel.

## Shapes

The shape language is **Soft (Level 1)**, leaning toward a technical, precision-cut look rather than a friendly, bubbly one. 

- **Standard Buttons & Inputs:** 0.25rem (4px) corner radius. This conveys stability and industrial strength.
- **Data Cards:** 0.5rem (8px) corner radius to subtly distinguish them from the background.
- **Interactive Icons:** Should be encased in circular or square containers with minimal rounding to maintain the "instrumental" aesthetic.

## Components

- **Buttons:** Primary buttons use a solid Electric Lime fill with black text. Secondary buttons use a ghost style with a 1px border. 
- **Cards:** Backgrounds must be #121212. Every card should feature a `label-caps` header to categorize the data inside (e.g., "SQUAT DEPTH", "PEAK VELOCITY").
- **Metrics/Data Viz:** Use thin (2px) strokes for line charts. For "Angle Tracking," use Cyber Blue lines with nodes that pulse when the target range is hit.
- **Chips:** Small, rectangular tags with 2px rounding. Use them for "Set Number," "Workout Type," or "Equipment."
- **Inputs:** Dark backgrounds with a bottom-border only or a subtle 1px outline. The caret and active border must be the Primary color.
- **Progress Rings:** High-stroke weight (at least 8px) to be visible from a distance, utilizing the Primary-to-Secondary gradient for intensity phases.