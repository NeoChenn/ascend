import { Link } from 'react-router-dom'
import styles from './Home.module.css'

export default function Home() {
  return (
    <main className={styles.container}>
      <h1>Ascend</h1>
      <p className={styles.subtitle}>
        Skills aren't given here — they're earned.
      </p>
      <div className={styles.features}>
        <div className={styles.featureItem}>
          <span className={styles.featureLabel}>Form analysis</span>
          <span className={styles.featureText}>Upload a video of your attempt. MediaPipe breaks it down frame by frame — you see exactly which form checks passed and what to fix.</span>
        </div>
        <div className={styles.featureItem}>
          <span className={styles.featureLabel}>Earn it, own it</span>
          <span className={styles.featureText}>Unlock a skill and your attempt becomes its showcase on the node — proof it's been conquered. Come back and beat yourself to claim a cleaner rep.</span>
        </div>
        <div className={styles.featureItem}>
          <span className={styles.featureLabel}>No shortcuts</span>
          <span className={styles.featureText}>Skills unlock in sequence. Prove the foundation before the harder progressions open up.</span>
        </div>
      </div>

      <div className={styles.actions}>
        <Link to="/skill-tree" className={styles.primaryButton}>View skill trees</Link>
        <Link to="/signup" className={styles.secondaryButton}>Create account</Link>
      </div>
    </main>
  )
}
