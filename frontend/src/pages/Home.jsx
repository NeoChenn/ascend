import { Link } from 'react-router-dom'
import styles from './Home.module.css'

export default function Home() {
  return (
    <main className={styles.container}>
      <h1>Calisthenics Coach</h1>
      <p className={styles.subtitle}>
        Upload a video of your movement and get instant form feedback powered by pose estimation.
      </p>
      <div className={styles.actions}>
        <Link to="/upload" className={styles.primaryButton}>Upload a video</Link>
        <Link to="/skill-tree" className={styles.secondaryButton}>View skill tree</Link>
      </div>
    </main>
  )
}
