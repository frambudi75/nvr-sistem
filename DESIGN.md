# NVR Design Direction

## Identity & Purpose
A mission-critical CCTV & NVR Management Console designed for security operators and administrators. Clean, utilitarian, and fast, prioritizing real-time video feed readability, system reliability, and responsive controls over decorative flair.

## Visual Direction & Dials
- **ENERGY**: 2 (Focused, clean, authoritative surveillance interface)
- **RHYTHM**: 2 (Structured layout matching content: live matrix, timeline scrubbers, camera cards, system telemetry)
- **MOTION**: 1 (Immediate functional response: 150ms-250ms opacity/color transitions; zero distracting bounces, float animations, or floating bubbles)

## Color System
- **Base Surfaces**: Deep night charcoal (`#030712`, `#0b1120`, `#0f172a`), providing optimal contrast for multi-channel video playback and low eye-strain in dark control rooms.
- **Borders & Dividers**: Subtle slate borders (`rgba(255, 255, 255, 0.08)` to `#1e293b`), creating clean boundaries without glowing outlines.
- **Typography & High Contrast**:
  - Primary text: Crisp white (`#f8fafc`) with minimum 10:1 contrast ratio against dark cards.
  - Secondary text / metadata: Slate (`#94a3b8`, `#cbd5e1`) maintaining WCAG AA minimum 4.5:1.
- **Purposeful Semantic Accents**:
  - Status Active / Live: Emerald (`#10b981`)
  - Recording Active: Crimson / Red (`#ef4444`)
  - Primary Action / Select: Sky Blue (`#0284c7` / `#38bdf8`)
  - Sub-Stream Indicator: Cyan (`#06b6d4`)
  - Detection Active: Violet (`#a855f7`)
  - Attention / Alert: Amber (`#f59e0b`)

## Typography Rules
- **UI & Controls**: Modern legible sans-serif (`Inter`, `system-ui`, `-apple-system`, `sans-serif`).
- **Telemetry & Timecodes**: Monospace (`JetBrains Mono`, `Fira Code`, `monospace`) strictly used for time codes (`HH:MM:SS`), timestamps (`YYYY-MM-DD`), RTSP URLs, and IP addresses for column alignment.
- **Copywriting**: Direct, honest technical vocabulary. No generic AI buzzwords ("revolutionary", "next-gen", "AI-powered magic"). Real human and motion detection labeled as "AI Detection" or "Human Detection". No em dashes (`—`).

## Functional Integrity (Anti-Slop Hard Gates)
- Every button, toggle, and dropdown must perform an actual operation or be removed.
- All modals must be closable via both `Esc` key and clear close button.
- Video playback controls must provide instant feedback, keyframe jumping, and accurate timecode synchronization.
- Theme: Purpose-built Dark Command Center (standard for surveillance/CCTV dashboards).
