// Stick-figure icons — 40×40 viewBox, strokeWidth 6.
// Thick round-capped lines read as filled silhouettes at 52px node size.
// All colours driven by currentColor (CSS `color` on the parent node).

const s = {
  stroke: 'currentColor',
  strokeWidth: 6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  fill: 'none',
}

// Slightly thinner style for bars / equipment
const b = {
  stroke: 'currentColor',
  strokeWidth: 4,
  strokeLinecap: 'round',
  fill: 'none',
}

// Silhouette style (v2) — thick round caps read as solid body mass at 52px display size.
// sT = torso (~13px), sU = upper limbs/thighs (~9px), sL = forearms/shins (~6.5px).
const sT = { stroke: 'currentColor', strokeWidth: 10, strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' }
const sU = { stroke: 'currentColor', strokeWidth: 7,  strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' }
const sL = { stroke: 'currentColor', strokeWidth: 5,  strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' }

function Head({ cx, cy, r = 5.5 }) {
  return <circle cx={cx} cy={cy} r={r} fill="currentColor" />
}

// Filled joint dot — adds visual mass at shoulder / hip connection points
function Dot({ cx, cy, r = 3 }) {
  return <circle cx={cx} cy={cy} r={r} fill="currentColor" />
}

// ─── PUSH TRACK ───────────────────────────────────────────────────────────────

export function PushUpIcon({ className }) {
  // Front-facing: head top, arms spread slightly downward, legs close together
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={6} r={5.5} />
      <line {...sT} x1={20} y1={12} x2={20} y2={26} />   {/* body              */}
      <line {...sU} x1={20} y1={13} x2={10} y2={19} />   {/* left arm          */}
      <line {...sU} x1={20} y1={13} x2={30} y2={19} />   {/* right arm         */}
      <line {...sU} x1={20} y1={26} x2={18} y2={36} />   {/* left leg          */}
      <line {...sU} x1={20} y1={26} x2={22} y2={36} />   {/* right leg         */}
    </svg>
  )
}

export function BentArmPlancheIcon({ className }) {
  // Front-facing: upper arms go out, forearms hang down — bent elbow visible from front
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={6} r={5} />
      <line {...sT} x1={20} y1={12} x2={20} y2={26} />   {/* body                */}
      <line {...sU} x1={20} y1={11} x2={13} y2={18} />   {/* left upper arm down  */}
      <line {...sL} x1={13} y1={18} x2={13} y2={26} />   {/* left forearm vert    */}
      <line {...sU} x1={20} y1={11} x2={27} y2={18} />   {/* right upper arm down */}
      <line {...sL} x1={27} y1={18} x2={27} y2={26} />   {/* right forearm vert   */}
      <line {...sU} x1={20} y1={26} x2={18} y2={36} />   {/* left leg            */}
      <line {...sU} x1={20} y1={26} x2={22} y2={36} />   {/* right leg           */}
    </svg>
  )
}

export function HandstandIcon({ className }) {
  // Inverted: straight arms from floor, head between arms, torso+legs up
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...sU} x1={13} y1={37} x2={16} y2={21} />  {/* L arm straight up     */}
      <line {...sU} x1={27} y1={37} x2={24} y2={21} />  {/* R arm straight up     */}
      <Head cx={20} cy={27} r={5} />                     {/* head between arms     */}
      <line {...sT} x1={20} y1={21} x2={20} y2={9}  />  {/* torso toward ceiling  */}
      <line {...sU} x1={20} y1={9}  x2={14} y2={3}  />  {/* L leg                 */}
      <line {...sU} x1={20} y1={9}  x2={26} y2={3}  />  {/* R leg                 */}
    </svg>
  )
}

export function ArcherPushUpIcon({ className }) {
  // Front-facing: right arm extends wide, left arm bent with forearm hanging down
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={6} r={5} />
      <line {...sT} x1={20} y1={12} x2={20} y2={26} />   {/* body                */}
      <line {...sU} x1={20} y1={13} x2={33} y2={10} />   {/* right arm extended  */}
      <line {...sU} x1={20} y1={13} x2={10} y2={15} />   {/* left upper arm      */}
      <line {...sL} x1={10} y1={15} x2={11} y2={23} />   {/* left forearm down   */}
      <line {...sU} x1={20} y1={26} x2={18} y2={36} />   {/* left leg            */}
      <line {...sU} x1={20} y1={26} x2={22} y2={36} />   {/* right leg           */}
    </svg>
  )
}

export function StraddlePlancheIcon({ className }) {
  // Front-facing: arms spread nearly horizontal, legs spread wide in straddle — star shape
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={6} r={5} />
      <line {...sT} x1={20} y1={12} x2={20} y2={26} />   {/* body               */}
      <line {...sU} x1={20} y1={13} x2={10} y2={19} />   {/* left arm           */}
      <line {...sU} x1={20} y1={13} x2={30} y2={19} />   {/* right arm          */}
      <line {...sU} x1={20} y1={26} x2={6}  y2={36} />   {/* left straddle leg  */}
      <line {...sU} x1={20} y1={26} x2={34} y2={36} />   {/* right straddle leg */}
    </svg>
  )
}

export function HandstandPushUpIcon({ className }) {
  // Inverted: bracket arms — forearms vertical, upper arms horizontal (90° arm bend)
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...sU} x1={6}  y1={36} x2={6}  y2={22} />  {/* L forearm vertical  */}
      <line {...sU} x1={6}  y1={22} x2={15} y2={22} />  {/* L upper arm horiz   */}
      <line {...sU} x1={34} y1={36} x2={34} y2={22} />  {/* R forearm vertical  */}
      <line {...sU} x1={34} y1={22} x2={25} y2={22} />  {/* R upper arm horiz   */}
      <Head cx={20} cy={30} r={5} />                     {/* head inside bracket */}
      <line {...sT} x1={20} y1={22} x2={20} y2={9}  />  {/* torso               */}
      <line {...sU} x1={20} y1={9}  x2={14} y2={3}  />  {/* L leg               */}
      <line {...sU} x1={20} y1={9}  x2={26} y2={3}  />  {/* R leg               */}
    </svg>
  )
}

export function OneArmPushUpIcon({ className }) {
  // Front-facing: single arm extends right, short stub left = free arm tucked behind back
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={6} r={5} />
      <line {...sT} x1={20} y1={12} x2={20} y2={26} />   {/* body                     */}
      <line {...sU} x1={20} y1={13} x2={10} y2={15} />   {/* left upper arm (support) */}
      <line {...sL} x1={10} y1={15} x2={11} y2={23} />   {/* left forearm down        */}
      <line {...sU} x1={20} y1={13} x2={26} y2={14} />   {/* right shoulder visible   */}
      <line {...sL} x1={26} y1={14} x2={23} y2={22} />   {/* forearm behind back      */}
      <line {...sU} x1={20} y1={26} x2={18} y2={36} />   {/* left leg                */}
      <line {...sU} x1={20} y1={26} x2={22} y2={36} />   {/* right leg               */}
    </svg>
  )
}

export function NinetyDegHSPUIcon({ className }) {
  // Inverted: diagonal bent arms, head low near floor
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...sU} x1={13} y1={37} x2={7}  y2={27} />  {/* L upper arm         */}
      <line {...sL} x1={7}  y1={27} x2={17} y2={22} />  {/* L forearm           */}
      <line {...sU} x1={27} y1={37} x2={33} y2={27} />  {/* R upper arm         */}
      <line {...sL} x1={33} y1={27} x2={23} y2={22} />  {/* R forearm           */}
      <Head cx={20} cy={33} r={5} />                     {/* head near floor     */}
      <line {...sT} x1={20} y1={22} x2={20} y2={9}  />  {/* torso               */}
      <line {...sU} x1={20} y1={9}  x2={14} y2={3}  />  {/* L leg               */}
      <line {...sU} x1={20} y1={9}  x2={26} y2={3}  />  {/* R leg               */}
    </svg>
  )
}

// ─── PULL TRACK ───────────────────────────────────────────────────────────────

export function PullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={4}  y1={3}  x2={36} y2={3}  />   {/* bar             */}
      <line {...sU} x1={11} y1={3}  x2={7}  y2={10} />   {/* L upper arm     */}
      <line {...sL} x1={7}  y1={10} x2={18} y2={15} />   {/* L forearm       */}
      <line {...sU} x1={29} y1={3}  x2={33} y2={10} />   {/* R upper arm     */}
      <line {...sL} x1={33} y1={10} x2={22} y2={15} />   {/* R forearm       */}
      <Head cx={20} cy={16} r={6} />
      <line {...sT} x1={20} y1={22} x2={20} y2={30} />   {/* torso           */}
      <line {...sU} x1={20} y1={30} x2={15} y2={38} />   {/* left leg        */}
      <line {...sU} x1={20} y1={30} x2={25} y2={38} />   {/* right leg       */}
    </svg>
  )
}

export function ExplosivePullUpIcon({ className }) {
  // Head breaks above bar level — chin over bar shows the explosive high position.
  // Elbows swept wide and back = aggressive pull force, distinct from a regular pull-up.
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={4}  y1={4}  x2={36} y2={4}  />   {/* bar                      */}
      <line {...sU} x1={11} y1={4}  x2={5}  y2={10} />   {/* L upper arm wide back    */}
      <line {...sL} x1={5}  y1={10} x2={17} y2={14} />   {/* L forearm to shoulder    */}
      <line {...sU} x1={29} y1={4}  x2={35} y2={10} />   {/* R upper arm wide back    */}
      <line {...sL} x1={35} y1={10} x2={23} y2={14} />   {/* R forearm to shoulder    */}
      <Head cx={20} cy={7}  r={5}  />                     {/* head breaks above bar    */}
      <line {...sT} x1={20} y1={14} x2={20} y2={24} />   {/* torso                    */}
      <line {...sU} x1={20} y1={24} x2={15} y2={33} />   {/* left leg                 */}
      <line {...sU} x1={20} y1={24} x2={25} y2={33} />   {/* right leg                */}
    </svg>
  )
}

export function MuscleUpIcon({ className }) {
  // Body fully above bar, arms spread to bar, legs hanging below
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={4}  y1={21} x2={36} y2={21} />   {/* bar — body is above it  */}
      <Head cx={20} cy={6} r={5} />
      <line {...sT} x1={20} y1={11} x2={20} y2={21} />   {/* torso above bar         */}
      <line {...sU} x1={17} y1={14} x2={10} y2={21} />   {/* left arm to bar         */}
      <line {...sU} x1={23} y1={14} x2={30} y2={21} />   {/* right arm to bar        */}
      <line {...sU} x1={20} y1={21} x2={15} y2={32} />   {/* left leg below bar      */}
      <line {...sU} x1={20} y1={21} x2={25} y2={32} />   {/* right leg below bar     */}
    </svg>
  )
}

export function ArcherPullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={4}  y1={3}  x2={36} y2={3}  />
      <line {...sU} x1={12} y1={3}  x2={7}  y2={10} />   {/* L upper arm (bent)       */}
      <line {...sL} x1={7}  y1={10} x2={17} y2={15} />   {/* L forearm               */}
      <line {...sU} x1={22} y1={20} x2={36} y2={3}  />   {/* R arm extended to bar end */}
      <Head cx={20} cy={16} r={6} />
      <line {...sT} x1={20} y1={22} x2={20} y2={30} />   {/* torso                   */}
      <line {...sU} x1={20} y1={30} x2={15} y2={38} />   {/* left leg                */}
      <line {...sU} x1={20} y1={30} x2={25} y2={38} />   {/* right leg               */}
    </svg>
  )
}

export function StraddleFrontLeverIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={3}  y1={13} x2={30} y2={13} />   {/* bar (extended)           */}
      <line {...sU} x1={22} y1={13} x2={22} y2={22} />   {/* single arm               */}
      <line {...sT} x1={10} y1={22} x2={29} y2={22} />   {/* horizontal body          */}
      <Head cx={35} cy={19} r={5} />                      {/* head offset from body cap */}
      <line {...sU} x1={10} y1={22} x2={3}  y2={22} />   {/* straddle leg             */}
    </svg>
  )
}

export function OneArmPullUpIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={4}  y1={3}  x2={30} y2={3}  />   {/* bar                    */}
      <line {...sU} x1={12} y1={3}  x2={7}  y2={10} />   {/* upper arm              */}
      <line {...sL} x1={7}  y1={10} x2={18} y2={15} />   {/* forearm                */}
      <Head cx={20} cy={16} r={6} />
      <line {...sT} x1={20} y1={22} x2={20} y2={30} />   {/* torso                  */}
      <line {...sU} x1={20} y1={22} x2={26} y2={23} />   {/* free arm shoulder       */}
      <line {...sL} x1={26} y1={23} x2={25} y2={30} />   {/* free arm tucked to body */}
      <line {...sU} x1={20} y1={30} x2={15} y2={38} />   {/* left leg               */}
      <line {...sU} x1={20} y1={30} x2={25} y2={38} />   {/* right leg              */}
    </svg>
  )
}

// ─── CORE TRACK ───────────────────────────────────────────────────────────────

export function LegRaiseIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={4}  y1={3}  x2={36} y2={3}  />  {/* bar                    */}
      <line {...sU} x1={13} y1={3}  x2={13} y2={22} />  {/* L arm straight         */}
      <line {...sU} x1={27} y1={3}  x2={27} y2={22} />  {/* R arm straight         */}
      <Head cx={20} cy={17} r={5} />
      <line {...sT} x1={20} y1={22} x2={20} y2={30} />  {/* torso                  */}
      <line {...sU} x1={20} y1={30} x2={36} y2={28} />  {/* legs horizontal — top  */}
      <line {...sU} x1={20} y1={30} x2={36} y2={32} />  {/* legs horizontal — bot  */}
    </svg>
  )
}

export function ToesToBarIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={3}  y1={3}  x2={36} y2={3}  />  {/* bar                    */}
      <line {...sU} x1={13} y1={3}  x2={13} y2={15} />  {/* L arm                  */}
      <line {...sU} x1={23} y1={3}  x2={23} y2={15} />  {/* R arm                  */}
      <Head cx={18} cy={20} r={5} />
      <line {...sU} x1={18} y1={25} x2={18} y2={34} />  {/* torso (sU = cleaner hip junction) */}
      <line {...sU} x1={18} y1={34} x2={35} y2={3}  />  {/* leg arcing up to bar   */}
    </svg>
  )
}

export function LSitIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={11} cy={8} r={5.5} />
      <line {...sT} x1={11} y1={14} x2={11} y2={25} />   {/* torso (upright) */}
      <line {...sU} x1={11} y1={19} x2={5}  y2={33} />   {/* near arm        */}
      <line {...sU} x1={11} y1={19} x2={17} y2={33} />   {/* far arm         */}
      <line {...sU} x1={11} y1={25} x2={37} y2={23} />   {/* upper leg       */}
      <line {...sU} x1={11} y1={25} x2={37} y2={27} />   {/* lower leg       */}
    </svg>
  )
}

export function OneArmToesToBarIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <line {...b}  x1={3}  y1={3}  x2={36} y2={3}  />  {/* bar                    */}
      <line {...sU} x1={18} y1={3}  x2={18} y2={15} />  {/* single arm             */}
      <Head cx={18} cy={20} r={5} />
      <line {...sU} x1={18} y1={25} x2={18} y2={34} />  {/* torso (sU = cleaner hip junction) */}
      <line {...sU} x1={18} y1={34} x2={35} y2={3}  />  {/* leg arcing up to bar   */}
    </svg>
  )
}

// ─── LEGS TRACK ───────────────────────────────────────────────────────────────

export function SquatIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={5} r={5.5} />
      <line {...sT} x1={20} y1={11} x2={20} y2={21} />   {/* torso           */}
      <line {...sL} x1={20} y1={16} x2={9}  y2={14} />   {/* left arm        */}
      <line {...sL} x1={20} y1={16} x2={31} y2={14} />   {/* right arm       */}
      <line {...sU} x1={20} y1={21} x2={11} y2={30} />   {/* left thigh      */}
      <line {...sU} x1={20} y1={21} x2={29} y2={30} />   {/* right thigh     */}
      <line {...sL} x1={11} y1={30} x2={12} y2={38} />   {/* left shin       */}
      <line {...sL} x1={29} y1={30} x2={28} y2={38} />   {/* right shin      */}
    </svg>
  )
}

export function BulgarianSplitSquatIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={14} cy={4} r={5} />
      <line {...sT} x1={14} y1={9}  x2={14} y2={20} />  {/* torso                */}
      <line {...sL} x1={14} y1={15} x2={5}  y2={19} />  {/* left arm             */}
      <line {...sL} x1={14} y1={15} x2={23} y2={19} />  {/* right arm            */}
      <line {...sU} x1={14} y1={20} x2={9}  y2={30} />  {/* front thigh          */}
      <line {...sL} x1={9}  y1={30} x2={8}  y2={38} />  {/* front shin           */}
      <line {...sU} x1={14} y1={20} x2={26} y2={24} />  {/* rear thigh           */}
      <line {...sL} x1={26} y1={24} x2={30} y2={17} />  {/* rear shin — going up */}
      <line {...b}  x1={27} y1={17} x2={37} y2={17} />  {/* elevated surface     */}
    </svg>
  )
}

export function PistolSquatIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={8} cy={5} r={5} />
      <line {...sT} x1={11} y1={10} x2={13} y2={22} />  {/* torso (slight fwd lean) */}
      <line {...sL} x1={12} y1={16} x2={27} y2={13} />  {/* arms forward (balance)  */}
      <line {...sU} x1={13} y1={22} x2={31} y2={19} />  {/* free leg horizontal     */}
      <line {...sU} x1={13} y1={22} x2={18} y2={31} />  {/* squat thigh             */}
      <line {...sL} x1={18} y1={31} x2={16} y2={39} />  {/* squat shin — vertical   */}
    </svg>
  )
}

// ─── DEFAULT ──────────────────────────────────────────────────────────────────

export function DefaultIcon({ className }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <Head cx={20} cy={7} />
      <line {...s} x1={20} y1={13} x2={20} y2={26} />
      <line {...s} x1={20} y1={18} x2={12} y2={14} />
      <line {...s} x1={20} y1={18} x2={28} y2={14} />
      <Dot cx={20} cy={18} />
      <Dot cx={20} cy={26} />
      <line {...s} x1={20} y1={26} x2={14} y2={35} />
      <line {...s} x1={20} y1={26} x2={26} y2={35} />
    </svg>
  )
}
