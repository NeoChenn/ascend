import styles from './SkillNode.module.css'

// A single skill card in the track chain.
// state: 'locked' | 'unlockable' | 'unlocked'
// trackColor: the hex colour for this track (e.g. '#f59e0b' for push)
// prerequisiteName: name of the required skill, shown on locked cards
// onClick: fires when state is 'unlockable' or 'unlocked'
export default function SkillNode({ skill, state, trackColor, prerequisiteName, onClick }) {
  const isLocked = state === 'locked'
  const isUnlocked = state === 'unlocked'
  const isUnlockable = state === 'unlockable'

  return (
    <div
      className={`${styles.node} ${styles[state]}`}
      style={{
        borderColor: isUnlockable || isUnlocked ? trackColor : undefined,
        backgroundColor: isUnlocked ? trackColor : undefined,
        cursor: 'pointer',
        // Glow effect on unlockable cards uses the track colour at low opacity
        boxShadow: isUnlockable ? `0 0 16px ${trackColor}33` : undefined,
      }}
      onClick={onClick}
    >
      <div className={styles.header}>
        <span className={styles.name}>{skill.name}</span>
        {isLocked && <span className={styles.icon}>🔒</span>}
        {isUnlocked && <span className={styles.icon}>✓</span>}
      </div>

      {/* Show which skill must be unlocked first */}
      {isLocked && prerequisiteName && (
        <p className={styles.prereq}>Requires: {prerequisiteName}</p>
      )}
    </div>
  )
}
