import styles from './SkillNode.module.css'

// Maps Supabase skill names to filenames in /public/icons/.
// Drop a PNG or SVG with a transparent background for any skill name listed here.
// Any skill not listed falls back to DefaultIcon (generic standing figure).
const SKILL_ICON_FILES = {
  'Push-up':               'push_up.png',
  'Bent Arm Planche':      'bent_arm_planche.png',
  'Handstand':             'handstand.png',
  'Archer Push-up':        'archer_push_up.png',
  'Straddle Planche':      'planche.png',
  'Handstand Push-up':     'handstand_push_up.png',
  'One-arm Push-up':       'one_arm_push_up.png',
  '90° Handstand Push-up': 'handstand_push_up.png',
  'Pull-up':               'pull_up.png',
  'Explosive Pull-up':     'pull_up.png',
  'Muscle-up':             'muscle_up.png',
  'Archer Pull-up':        'archer_pull_up.png',
  'Straddle Front Lever':  'front_lever.png',
  'One-arm Pull-up':       'one_arm_pull_up.png',
  'Leg Raise':             'leg_raise.png',
  'Toes to Bar':           'toes_to_bar.png',
  'L-sit':                 'l_sit.png',
  'One-arm Toes to Bar':   'toes_to_bar.png',
  'Squat':                 'squat.png',
  'Bulgarian Split Squat': 'split_squat.png',
  'Pistol Squat':          'pistol_squat.png',
}

// Generic fallback — shown until a real image is dropped into /public/icons/
function DefaultIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <circle cx={20} cy={7} r={5} fill="currentColor" />
      <line stroke="currentColor" strokeWidth={6} strokeLinecap="round" x1={20} y1={13} x2={20} y2={26} />
      <line stroke="currentColor" strokeWidth={6} strokeLinecap="round" x1={20} y1={18} x2={12} y2={14} />
      <line stroke="currentColor" strokeWidth={6} strokeLinecap="round" x1={20} y1={18} x2={28} y2={14} />
      <line stroke="currentColor" strokeWidth={6} strokeLinecap="round" x1={20} y1={26} x2={14} y2={35} />
      <line stroke="currentColor" strokeWidth={6} strokeLinecap="round" x1={20} y1={26} x2={26} y2={35} />
    </svg>
  )
}

// state:             'locked' | 'unlockable' | 'unlocked'
// trackColor:        hex colour for this track (e.g. '#f59e0b' for push)
// triggerUnlockAnim: set true by TrackPage for one render-cycle after the modal
//                    closes following a pass — fires the burst animation
// onClick:           always fires — all states open the modal
export default function SkillNode({ skill, state, trackColor, triggerUnlockAnim = false, onClick }) {
  const isUnlocked   = state === 'unlocked'
  const isUnlockable = state === 'unlockable'

  const iconFile = SKILL_ICON_FILES[skill.name]

  const circleStyle = {
    borderColor:     isUnlockable || isUnlocked ? trackColor : undefined,
    backgroundColor: isUnlocked ? trackColor : undefined,
    color:           isUnlocked ? 'white' : isUnlockable ? trackColor : undefined,
    boxShadow: triggerUnlockAnim
      ? `0 0 28px ${trackColor}, 0 0 56px ${trackColor}88`
      : isUnlocked
      ? `0 0 10px ${trackColor}, 0 0 24px ${trackColor}bb, 0 0 48px ${trackColor}55`
      : isUnlockable
      ? `0 0 14px ${trackColor}55`
      : undefined,
  }

  return (
    <div
      className={`${styles.nodeWrapper} ${styles[state]}`}
      onClick={onClick}
    >
      <div
        className={`${styles.circle} ${triggerUnlockAnim ? styles.justUnlocked : ''}`}
        style={circleStyle}
      >
        {iconFile ? (
          <img
            src={`/icons/${iconFile}`}
            alt={skill.name}
            className={`${styles.skillIconImg} ${styles[`icon_${state}`]}`}
          />
        ) : (
          <DefaultIcon className={styles.skillIcon} />
        )}
      </div>
    </div>
  )
}
