// Stick-figure SVG icons for each skill, rendered inside the circular skill nodes.
//
// Design rules:
//   - ViewBox 0 0 40 40
//   - All lines/paths use stroke="currentColor" fill="none"
//   - Head circle uses fill="currentColor"
//   - Parent CSS `color` controls the entire icon colour automatically
//   - strokeWidth 2, strokeLinecap "round", strokeLinejoin "round"
//
// Orientation:
//   - Horizontal exercises: person faces RIGHT (head on right side)
//   - Hanging exercises: bar at top
//   - Ground standing exercises: head at top

const s = {
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  fill: 'none',
}

function Head({ cx, cy, r = 3 }) {
  return <circle cx={cx} cy={cy} r={r} fill="currentColor" />
}

// ─── PUSH TRACK ───────────────────────────────────────────────────────────────

// Side view plank: body horizontal, arms straight down, feet on ground
export function PushUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={34} cy={11} />
      <line {...s} x1={31} y1={14} x2={8} y2={18} />
      <line {...s} x1={26} y1={15} x2={23} y2={25} />
      <line {...s} x1={17} y1={17} x2={14} y2={25} />
      <line {...s} x1={8}  y1={18} x2={5}  y2={25} />
      <line {...s} x1={12} y1={19} x2={9}  y2={26} />
    </svg>
  )
}

// Horizontal body floating (no feet on ground), arms bent with visible elbows
export function BentArmPlancheIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={34} cy={14} />
      <line {...s} x1={31} y1={16} x2={8} y2={16} />
      <path {...s} d="M 26 16 L 22 23 L 18 21" />
      <path {...s} d="M 14 16 L 10 23 L 6  21" />
      <line {...s} x1={8} y1={16} x2={3} y2={12} />
      <line {...s} x1={8} y1={16} x2={3} y2={20} />
    </svg>
  )
}

// Inverted vertical: hands at bottom, arms straight, legs at top
export function HandstandIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={28} />
      <line {...s} x1={12} y1={36} x2={16} y2={22} />
      <line {...s} x1={28} y1={36} x2={24} y2={22} />
      <line {...s} x1={20} y1={22} x2={20} y2={8}  />
      <line {...s} x1={20} y1={8}  x2={15} y2={2}  />
      <line {...s} x1={20} y1={8}  x2={25} y2={2}  />
    </svg>
  )
}

// Push-up position with one arm extended straight sideways (back)
export function ArcherPushUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={34} cy={11} />
      <line {...s} x1={31} y1={14} x2={8}  y2={18} />
      <line {...s} x1={25} y1={15} x2={23} y2={25} />
      <line {...s} x1={16} y1={17} x2={4}  y2={15} />
      <line {...s} x1={8}  y1={18} x2={5}  y2={25} />
      <line {...s} x1={12} y1={19} x2={9}  y2={26} />
    </svg>
  )
}

// Horizontal floating, arms straight down, legs spread wide (V shape at back)
export function StraddlePlancheIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={34} cy={14} />
      <line {...s} x1={31} y1={16} x2={8}  y2={16} />
      <line {...s} x1={26} y1={16} x2={24} y2={26} />
      <line {...s} x1={16} y1={16} x2={14} y2={26} />
      <line {...s} x1={8}  y1={16} x2={3}  y2={10} />
      <line {...s} x1={8}  y1={16} x2={3}  y2={22} />
    </svg>
  )
}

// Inverted with bent arms — elbows form a visible point on each side
export function HandstandPushUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={30} />
      <path {...s} d="M 12 36 L 14 27 L 16 22" />
      <path {...s} d="M 28 36 L 26 27 L 24 22" />
      <line {...s} x1={20} y1={22} x2={20} y2={8} />
      <line {...s} x1={20} y1={8}  x2={15} y2={2} />
      <line {...s} x1={20} y1={8}  x2={25} y2={2} />
    </svg>
  )
}

// Push-up: one arm supporting below, other arm raised sideways
export function OneArmPushUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={34} cy={11} />
      <line {...s} x1={31} y1={14} x2={8}  y2={18} />
      <line {...s} x1={20} y1={16} x2={18} y2={26} />
      <line {...s} x1={26} y1={15} x2={30} y2={21} />
      <line {...s} x1={8}  y1={18} x2={3}  y2={24} />
      <line {...s} x1={13} y1={19} x2={9}  y2={26} />
    </svg>
  )
}

// Inverted with very wide flared elbows — distinguishes from regular HSPU
export function NinetyDegHSPUIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={31} />
      <path {...s} d="M 10 36 L 6  26 L 16 22" />
      <path {...s} d="M 30 36 L 34 26 L 24 22" />
      <line {...s} x1={20} y1={22} x2={20} y2={8} />
      <line {...s} x1={20} y1={8}  x2={15} y2={2} />
      <line {...s} x1={20} y1={8}  x2={25} y2={2} />
    </svg>
  )
}

// ─── PULL TRACK ───────────────────────────────────────────────────────────────

// Hanging vertically, arms extended up to bar, body straight
export function PullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={8}  y1={4} x2={32} y2={4} />
      <Head cx={20} cy={10} />
      <line {...s} x1={20} y1={13} x2={12} y2={5} />
      <line {...s} x1={20} y1={13} x2={28} y2={5} />
      <line {...s} x1={20} y1={13} x2={20} y2={28} />
      <line {...s} x1={20} y1={28} x2={15} y2={36} />
      <line {...s} x1={20} y1={28} x2={25} y2={36} />
    </svg>
  )
}

// Chin above bar — bar is lower in the image, body raised above it
export function ExplosivePullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={8}  y1={14} x2={32} y2={14} />
      <Head cx={20} cy={6} />
      <line {...s} x1={20} y1={10} x2={12} y2={15} />
      <line {...s} x1={20} y1={10} x2={28} y2={15} />
      <line {...s} x1={20} y1={10} x2={20} y2={28} />
      <line {...s} x1={20} y1={28} x2={15} y2={36} />
      <line {...s} x1={20} y1={28} x2={25} y2={36} />
    </svg>
  )
}

// Body above bar in dip position — arms push DOWN onto bar from above
export function MuscleUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={8}  y1={20} x2={32} y2={20} />
      <Head cx={20} cy={6} />
      <line {...s} x1={20} y1={10} x2={10} y2={20} />
      <line {...s} x1={20} y1={10} x2={30} y2={20} />
      <line {...s} x1={20} y1={10} x2={20} y2={24} />
      <line {...s} x1={20} y1={24} x2={15} y2={34} />
      <line {...s} x1={20} y1={24} x2={25} y2={34} />
    </svg>
  )
}

// One arm pulling to bar (bent), other arm extended horizontally to side
export function ArcherPullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={8}  y1={4} x2={28} y2={4} />
      <Head cx={20} cy={10} />
      <line {...s} x1={20} y1={13} x2={14} y2={5}  />
      <line {...s} x1={20} y1={13} x2={34} y2={12} />
      <line {...s} x1={20} y1={13} x2={20} y2={28} />
      <line {...s} x1={20} y1={28} x2={15} y2={36} />
      <line {...s} x1={20} y1={28} x2={25} y2={36} />
    </svg>
  )
}

// Body horizontal face-up hanging from bar, legs spread (V shape at hips end)
export function StraddleFrontLeverIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={10} y1={6} x2={30} y2={6} />
      <line {...s} x1={10} y1={6} x2={10} y2={16} />
      <line {...s} x1={30} y1={6} x2={30} y2={16} />
      <line {...s} x1={10} y1={16} x2={30} y2={16} />
      <Head cx={34} cy={16} />
      <line {...s} x1={10} y1={16} x2={4}  y2={10} />
      <line {...s} x1={10} y1={16} x2={4}  y2={22} />
    </svg>
  )
}

// One arm gripping bar above, other arm hanging at side of body
export function OneArmPullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={10} y1={4} x2={26} y2={4} />
      <Head cx={20} cy={10} />
      <line {...s} x1={20} y1={13} x2={14} y2={5}  />
      <line {...s} x1={20} y1={13} x2={28} y2={20} />
      <line {...s} x1={20} y1={13} x2={20} y2={28} />
      <line {...s} x1={20} y1={28} x2={15} y2={36} />
      <line {...s} x1={20} y1={28} x2={25} y2={36} />
    </svg>
  )
}

// ─── CORE TRACK ───────────────────────────────────────────────────────────────

// Hanging, legs raised to 90° — legs horizontal forward
export function LegRaiseIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={8}  y1={4} x2={32} y2={4} />
      <Head cx={20} cy={10} />
      <line {...s} x1={20} y1={13} x2={12} y2={5} />
      <line {...s} x1={20} y1={13} x2={28} y2={5} />
      <line {...s} x1={20} y1={13} x2={20} y2={24} />
      <line {...s} x1={20} y1={24} x2={32} y2={22} />
      <line {...s} x1={20} y1={24} x2={32} y2={26} />
    </svg>
  )
}

// Hanging, pike fold — feet reach back up to the bar (inverted-V body shape)
export function ToesToBarIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={8}  y1={4} x2={32} y2={4} />
      <line {...s} x1={12} y1={4} x2={16} y2={14} />
      <line {...s} x1={28} y1={4} x2={24} y2={14} />
      <Head cx={20} cy={18} />
      <line {...s} x1={20} y1={14} x2={20} y2={26} />
      <line {...s} x1={20} y1={26} x2={13} y2={7} />
      <line {...s} x1={20} y1={26} x2={27} y2={7} />
    </svg>
  )
}

// Arms pressing down, body upright, legs horizontal forward — L shape
export function LSitIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={7} />
      <line {...s} x1={20} y1={10} x2={20} y2={24} />
      <line {...s} x1={20} y1={24} x2={12} y2={34} />
      <line {...s} x1={20} y1={24} x2={28} y2={34} />
      <line {...s} x1={20} y1={24} x2={36} y2={22} />
      <line {...s} x1={20} y1={24} x2={36} y2={26} />
    </svg>
  )
}

// One arm to bar, pike fold — same as toes to bar but one arm only
export function OneArmToesToBarIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...s} x1={10} y1={4} x2={26} y2={4} />
      <line {...s} x1={14} y1={4} x2={18} y2={14} />
      <line {...s} x1={18} y1={14} x2={26} y2={18} />
      <Head cx={22} cy={18} />
      <line {...s} x1={20} y1={14} x2={20} y2={26} />
      <line {...s} x1={20} y1={26} x2={14} y2={8} />
      <line {...s} x1={20} y1={26} x2={26} y2={8} />
    </svg>
  )
}

// ─── LEGS TRACK ───────────────────────────────────────────────────────────────

// Deep squat: head top, body upright, thighs wide, lower legs straight
export function SquatIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={5} />
      <line {...s} x1={20} y1={8}  x2={20} y2={20} />
      <line {...s} x1={20} y1={14} x2={10} y2={12} />
      <line {...s} x1={20} y1={14} x2={30} y2={12} />
      <line {...s} x1={20} y1={20} x2={10} y2={28} />
      <line {...s} x1={20} y1={20} x2={30} y2={28} />
      <line {...s} x1={10} y1={28} x2={10} y2={36} />
      <line {...s} x1={30} y1={28} x2={30} y2={36} />
    </svg>
  )
}

// Front leg bent, rear leg extended back on elevated surface (bench hint)
export function BulgarianSplitSquatIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={5} />
      <line {...s} x1={20} y1={8}  x2={20} y2={20} />
      <line {...s} x1={20} y1={14} x2={12} y2={18} />
      <line {...s} x1={12} y1={28} x2={12} y2={36} />
      <line {...s} x1={20} y1={20} x2={12} y2={28} />
      <line {...s} x1={20} y1={20} x2={32} y2={22} />
      <line {...s} x1={32} y1={22} x2={38} y2={22} />
      <line {...s} x1={38} y1={22} x2={38} y2={26} />
    </svg>
  )
}

// One leg in deep squat, other leg extended forward — pistol shape
export function PistolSquatIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={5} />
      <line {...s} x1={20} y1={8}  x2={20} y2={20} />
      <line {...s} x1={20} y1={14} x2={10} y2={12} />
      <line {...s} x1={20} y1={20} x2={18} y2={30} />
      <line {...s} x1={18} y1={30} x2={14} y2={38} />
      <line {...s} x1={20} y1={20} x2={36} y2={17} />
    </svg>
  )
}

// ─── DEFAULT ──────────────────────────────────────────────────────────────────

// Shown for any skill name not in the SKILL_ICONS map
export function DefaultIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={10} />
      <line {...s} x1={20} y1={13} x2={20} y2={26} />
      <line {...s} x1={20} y1={18} x2={12} y2={14} />
      <line {...s} x1={20} y1={18} x2={28} y2={14} />
      <line {...s} x1={20} y1={26} x2={14} y2={34} />
      <line {...s} x1={20} y1={26} x2={26} y2={34} />
    </svg>
  )
}
