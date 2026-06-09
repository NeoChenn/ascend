import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './SkillTree.module.css'

const TRACK_COLORS = {
  push: '#f59e0b',
  pull: '#60a5fa',
  core: '#a78bfa',
  legs: '#34d399',
}

const TRACK_LABELS = {
  push: 'Push',
  pull: 'Pull',
  core: 'Core',
  legs: 'Legs',
}

export default function SkillTree() {
  const [hoveredTrack, setHoveredTrack] = useState(null)
  const navigate = useNavigate()

  const handleClick = (track) => navigate(`/track/${track}`)

  // Returns SVG props for a muscle element belonging to the given track.
  // Highlighted when that track is hovered, dimmed otherwise.
  const muscle = (track) => ({
    fill: hoveredTrack === track ? TRACK_COLORS[track] : '#252525',
    stroke: hoveredTrack === track ? TRACK_COLORS[track] : '#3a3a3a',
    strokeWidth: 1,
    style: { transition: 'fill 0.15s ease, stroke 0.15s ease', cursor: 'pointer' },
    onMouseEnter: () => setHoveredTrack(track),
    onMouseLeave: () => setHoveredTrack(null),
    onClick: () => handleClick(track),
  })

  // Shared style for body silhouette parts — not interactive
  const body = {
    fill: '#1a1a1a',
    stroke: '#2e2e2e',
    strokeWidth: 1.5,
  }

  return (
    <main className={styles.container}>
      <h1 className={styles.title}>Skill Trees</h1>
      <p className={styles.subtitle}>Select a muscle group to explore that skill tree.</p>

      <div className={styles.mapWrapper}>
        <svg
          viewBox="0 0 200 460"
          className={styles.svg}
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* ── Body silhouette (base layer, not interactive) ── */}

          {/* Head */}
          <ellipse cx="100" cy="34" rx="26" ry="28" {...body} />
          {/* Neck */}
          <rect x="91" y="60" width="18" height="18" rx="4" {...body} />
          {/* Left shoulder cap */}
          <ellipse cx="57" cy="83" rx="19" ry="14" {...body} />
          {/* Right shoulder cap */}
          <ellipse cx="143" cy="83" rx="19" ry="14" {...body} />
          {/* Torso */}
          <path d="M60,78 L140,78 L148,168 L140,242 L60,242 L52,168 Z" {...body} />
          {/* Left upper arm */}
          <rect x="34" y="76" width="24" height="90" rx="11" {...body} />
          {/* Right upper arm */}
          <rect x="142" y="76" width="24" height="90" rx="11" {...body} />
          {/* Left forearm */}
          <rect x="36" y="163" width="20" height="80" rx="9" {...body} />
          {/* Right forearm */}
          <rect x="144" y="163" width="20" height="80" rx="9" {...body} />
          {/* Hips */}
          <ellipse cx="100" cy="248" rx="42" ry="13" {...body} />
          {/* Left thigh */}
          <rect x="60" y="246" width="34" height="90" rx="15" {...body} />
          {/* Right thigh */}
          <rect x="106" y="246" width="34" height="90" rx="15" {...body} />
          {/* Left calf */}
          <rect x="63" y="333" width="28" height="86" rx="12" {...body} />
          {/* Right calf */}
          <rect x="109" y="333" width="28" height="86" rx="12" {...body} />
          {/* Left foot */}
          <ellipse cx="75" cy="425" rx="17" ry="9" {...body} />
          {/* Right foot */}
          <ellipse cx="125" cy="425" rx="17" ry="9" {...body} />

          {/* ── Muscle overlays (interactive) ── */}

          {/* PUSH — chest, shoulders, triceps */}
          <ellipse cx="83"  cy="116" rx="20" ry="17" {...muscle('push')} />  {/* left pec */}
          <ellipse cx="117" cy="116" rx="20" ry="17" {...muscle('push')} />  {/* right pec */}
          <ellipse cx="52"  cy="87"  rx="17" ry="14" {...muscle('push')} />  {/* left deltoid */}
          <ellipse cx="148" cy="87"  rx="17" ry="14" {...muscle('push')} />  {/* right deltoid */}
          <ellipse cx="38"  cy="152" rx="10" ry="20" {...muscle('push')} />  {/* left tricep */}
          <ellipse cx="162" cy="152" rx="10" ry="20" {...muscle('push')} />  {/* right tricep */}

          {/* PULL — lats, biceps */}
          <ellipse cx="44"  cy="130" rx="10" ry="18" {...muscle('pull')} />  {/* left bicep */}
          <ellipse cx="156" cy="130" rx="10" ry="18" {...muscle('pull')} />  {/* right bicep */}
          <ellipse cx="61"  cy="162" rx="10" ry="30" {...muscle('pull')} />  {/* left lat */}
          <ellipse cx="139" cy="162" rx="10" ry="30" {...muscle('pull')} />  {/* right lat */}

          {/* CORE — abs, obliques */}
          <ellipse cx="100" cy="178" rx="17" ry="30" {...muscle('core')} />  {/* abs */}
          <ellipse cx="76"  cy="192" rx="10" ry="24" {...muscle('core')} />  {/* left oblique */}
          <ellipse cx="124" cy="192" rx="10" ry="24" {...muscle('core')} />  {/* right oblique */}

          {/* LEGS — quads, calves */}
          <ellipse cx="77"  cy="296" rx="15" ry="35" {...muscle('legs')} />  {/* left quad */}
          <ellipse cx="123" cy="296" rx="15" ry="35" {...muscle('legs')} />  {/* right quad */}
          <ellipse cx="75"  cy="382" rx="12" ry="25" {...muscle('legs')} />  {/* left calf */}
          <ellipse cx="125" cy="382" rx="12" ry="25" {...muscle('legs')} />  {/* right calf */}
        </svg>

        {/* Track legend — also clickable and drives hover state */}
        <div className={styles.legend}>
          {Object.entries(TRACK_LABELS).map(([track, label]) => (
            <button
              key={track}
              className={styles.legendItem}
              style={{
                color: hoveredTrack === track ? TRACK_COLORS[track] : '#a0a0a0',
                borderColor: hoveredTrack === track ? TRACK_COLORS[track] : '#2a2a2a',
              }}
              onMouseEnter={() => setHoveredTrack(track)}
              onMouseLeave={() => setHoveredTrack(null)}
              onClick={() => handleClick(track)}
            >
              <span
                className={styles.legendDot}
                style={{ background: TRACK_COLORS[track] }}
              />
              {label}
            </button>
          ))}
        </div>
      </div>
    </main>
  )
}
