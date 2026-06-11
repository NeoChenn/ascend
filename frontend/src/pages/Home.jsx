import { Link } from 'react-router-dom'
import styles from './Home.module.css'

export default function Home() {
  return (
    <main className={styles.container}>
      <h1>Ascend</h1>
      <p className={styles.subtitle}>
        Skills aren't given here — they're earned. Upload a video, pass the analysis, unlock the node.
      </p>
      <div className={styles.actions}>
        <Link to="/skill-tree" className={styles.primaryButton}>View skill trees</Link>
        <Link to="/signup" className={styles.secondaryButton}>Create account</Link>
      </div>
    </main>
  )
}
