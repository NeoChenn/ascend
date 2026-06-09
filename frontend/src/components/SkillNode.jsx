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

// state:             'locked' | 'unlockable' | 'unlocked'
// trackColor:        hex colour for this track (e.g. '#f59e0b' for push)
// isLeaf:            true for pinnacle skills (nothing else requires them) — renders as diamond
// triggerUnlockAnim: set true by TrackPage for one render-cycle after the modal
//                    closes following a pass — fires the burst animation
// onClick:           always fires — all states open the modal
export default function SkillNode({ skill, state, trackColor, isLeaf = false, triggerUnlockAnim = false, onClick }) {
  const isUnlocked   = state === 'unlocked'
  const isUnlockable = state === 'unlockable'

  const Icon = SKILL_ICONS[skill.name] ?? DefaultIcon

  // Inline styles drive the dynamic per-track colour.
  // CSS `color` propagates into the SVG via currentColor on every stroke/fill.
  // Use filter: drop-shadow instead of box-shadow — clip-path clips box-shadow but
  // drop-shadow applies after clipping, so it correctly follows the polygon outline.
  const circleStyle = {
    borderColor:     isUnlockable || isUnlocked ? trackColor : undefined,
    backgroundColor: isUnlocked ? trackColor : undefined,
    color:           isUnlocked ? 'white' : isUnlockable ? trackColor : undefined,
    filter: triggerUnlockAnim
      ? `drop-shadow(0 0 12px ${trackColor}) drop-shadow(0 0 24px ${trackColor}99)`
      : isUnlocked
      ? `drop-shadow(0 0 5px ${trackColor}) drop-shadow(0 0 14px ${trackColor}99) drop-shadow(0 0 28px ${trackColor}44)`
      : isUnlockable
      ? `drop-shadow(0 0 6px ${trackColor}66)`
      : undefined,
  }

  return (
    <div
      className={`${styles.nodeWrapper} ${styles[state]}`}
      onClick={onClick}
    >
      <div
        className={`${styles.circle} ${isLeaf ? styles.leaf : ''} ${triggerUnlockAnim ? styles.justUnlocked : ''}`}
        style={circleStyle}
      >
        <Icon className={styles.skillIcon} />
      </div>
    </div>
  )
}
