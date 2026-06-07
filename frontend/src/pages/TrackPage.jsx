import { useParams, Link } from 'react-router-dom'
import styles from './TrackPage.module.css'

const TRACK_LABELS = {
  push: 'Push',
  pull: 'Pull',
  core: 'Core',
  legs: 'Legs',
}

const TRACK_COLORS = {
  push: '#f59e0b',
  pull: '#60a5fa',
  core: '#a78bfa',
  legs: '#34d399',
}

export default function TrackPage() {
  // useParams reads the :trackId segment from the URL — e.g. /track/push gives { trackId: 'push' }
  const { trackId } = useParams()
  const label = TRACK_LABELS[trackId]
  const color = TRACK_COLORS[trackId]

  if (!label) {
    return (
      <main className={styles.container}>
        <p>Track not found.</p>
        <Link to="/skill-tree">← Back to skill tree</Link>
      </main>
    )
  }

  return (
    <main className={styles.container}>
      <Link to="/skill-tree" className={styles.back}>← Skill tree</Link>
      <h1 className={styles.title} style={{ color }}>
        {label} Track
      </h1>
      <p className={styles.subtitle}>Skills coming soon.</p>
    </main>
  )
}
