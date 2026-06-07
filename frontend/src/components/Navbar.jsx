import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Navbar.module.css'

export default function Navbar() {
  const { user, signOut } = useAuth()

  return (
    <nav className={styles.nav}>
      <Link to="/" className={styles.brand}>Ascend</Link>
      <div className={styles.links}>
        {user ? (
          <>
            <span className={styles.email}>{user.email}</span>
            <button className={styles.signOutButton} onClick={signOut}>Sign out</button>
          </>
        ) : (
          <>
            <Link to="/login">Sign in</Link>
            <Link to="/signup" className={styles.signUpLink}>Sign up</Link>
          </>
        )}
      </div>
    </nav>
  )
}
