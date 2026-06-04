import { Link } from 'react-router-dom'
import styles from './Navbar.module.css'

export default function Navbar() {
  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.brand}>Calisthenics Coach</Link>
      <div className={styles.links}>
        <Link to="/upload">Upload</Link>
        <Link to="/skill-tree">Skill Tree</Link>
      </div>
    </nav>
  )
}
