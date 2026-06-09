import { useState, useRef, useEffect } from 'react'
import styles from './SkillNode.module.css'
import {
  PushUpIcon,
  BentArmPlancheIcon,
  HandstandIcon,
  ArcherPushUpIcon,
  StraddlePlancheIcon,
  HandstandPushUpIcon,
  OneArmPushUpIcon,
  NinetyDegHSPUIcon,
  PullUpIcon,
  ExplosivePullUpIcon,
  MuscleUpIcon,
  ArcherPullUpIcon,
  StraddleFrontLeverIcon,
  OneArmPullUpIcon,
  LegRaiseIcon,
  ToesToBarIcon,
  LSitIcon,
  OneArmToesToBarIcon,
  SquatIcon,
  BulgarianSplitSquatIcon,
  PistolSquatIcon,
  DefaultIcon,
} from './SkillIcons'

// Maps Supabase skill names to their stick-figure icon components.
// Any skill not listed falls back to DefaultIcon (standing figure).
const SKILL_ICONS = {
  'Push-up':               PushUpIcon,
  'Bent Arm Planche':      BentArmPlancheIcon,
  'Handstand':             HandstandIcon,
  'Archer Push-up':        ArcherPushUpIcon,
  'Straddle Planche':      StraddlePlancheIcon,
  'Handstand Push-up':     HandstandPushUpIcon,
  'One-arm Push-up':       OneArmPushUpIcon,
  '90° Handstand Push-up': NinetyDegHSPUIcon,
  'Pull-up':               PullUpIcon,
  'Explosive Pull-up':     ExplosivePullUpIcon,
  'Muscle-up':             MuscleUpIcon,
  'Archer Pull-up':        ArcherPullUpIcon,
  'Straddle Front Lever':  StraddleFrontLeverIcon,
  'One-arm Pull-up':       OneArmPullUpIcon,
  'Leg Raise':             LegRaiseIcon,
  'Toes to Bar':           ToesToBarIcon,
  'L-sit':                 LSitIcon,
  'One-arm Toes to Bar':   OneArmToesToBarIcon,
  'Squat':                 SquatIcon,
  'Bulgarian Split Squat': BulgarianSplitSquatIcon,
  'Pistol Squat':          PistolSquatIcon,
}

// state: 'locked' | 'unlockable' | 'unlocked'
// trackColor: hex colour for this track (e.g. '#f59e0b' for push)
// onClick: always fires — all states open the modal
export default function SkillNode({ skill, state, trackColor, onClick }) {
  const isUnlocked   = state === 'unlocked'
  const isUnlockable = state === 'unlockable'

  // Detect the unlockable→unlocked transition and fire a brief pulse animation.
  const prevStateRef = useRef(state)
  const [justUnlocked, setJustUnlocked] = useState(false)

  useEffect(() => {
    if (prevStateRef.current !== 'unlocked' && state === 'unlocked') {
      setJustUnlocked(true)
      const timer = setTimeout(() => setJustUnlocked(false), 700)
      return () => clearTimeout(timer)
    }
    prevStateRef.current = state
  }, [state])

  const Icon = SKILL_ICONS[skill.name] ?? DefaultIcon

  // Inline styles drive the dynamic per-track colour.
  // CSS `color` propagates into the SVG via currentColor on every stroke/fill.
  const circleStyle = {
    borderColor:     isUnlockable || isUnlocked ? trackColor : undefined,
    backgroundColor: isUnlocked ? trackColor : undefined,
    color:           isUnlocked ? 'white' : isUnlockable ? trackColor : undefined,
    boxShadow: justUnlocked
      ? `0 0 28px ${trackColor}, 0 0 56px ${trackColor}55`
      : isUnlockable
      ? `0 0 16px ${trackColor}55`
      : undefined,
  }

  return (
    <div
      className={`${styles.nodeWrapper} ${styles[state]}`}
      onClick={onClick}
    >
      <div
        className={`${styles.circle} ${justUnlocked ? styles.justUnlocked : ''}`}
        style={circleStyle}
      >
        <Icon className={styles.skillIcon} />
      </div>
      <span className={styles.name}>{skill.name}</span>
    </div>
  )
}
