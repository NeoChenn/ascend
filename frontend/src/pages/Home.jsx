import { Link } from 'react-router-dom'
import styles from './Home.module.css'

export default function Home() {
  return (
    <main className={styles.container}>
      <h1>Ascend</h1>
      <p className={styles.subtitle}>
        Unlock calisthenics skills by proving your form. Upload a video, pass the analysis, earn the node.
      </p>
      <div className={styles.actions}>
        <Link to="/skill-tree" className={styles.primaryButton}>View body map</Link>
        <Link to="/signup" className={styles.secondaryButton}>Create account</Link>
      </div>
    </main>
  )
}
