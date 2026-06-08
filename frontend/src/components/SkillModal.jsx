import styles from './SkillModal.module.css'

// Modal shown when the user clicks an unlockable skill node.
// skill: the full skill row from Supabase
// trackColor: hex colour for this track
// onClose: called when the user dismisses the modal
export default function SkillModal({ skill, trackColor, onClose }) {
  if (!skill) return null

  // Close when clicking the dark backdrop behind the card
  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) onClose()
  }

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.card}>

        <button className={styles.closeButton} onClick={onClose} aria-label="Close">
          ×
        </button>

        <h2 className={styles.title} style={{ color: trackColor }}>
          {skill.name}
        </h2>

        {skill.description && (
          <p className={styles.description}>{skill.description}</p>
        )}

        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Filming instructions</h3>
          <p className={styles.instructions}>
            {skill.filming_instructions ?? 'Film from the side, full body in frame.'}
          </p>
        </div>

        {/* Upload button — wired up in the next step */}
        <button
          className={styles.uploadButton}
          style={{ backgroundColor: trackColor }}
          disabled
        >
          Upload attempt
        </button>

      </div>
    </div>
  )
}
