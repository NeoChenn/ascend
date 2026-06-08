import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { supabase } from '../supabaseClient'
import { useAuth } from '../context/AuthContext'
import SkillNode from '../components/SkillNode'
import SkillModal from '../components/SkillModal'
import styles from './TrackPage.module.css'

const TRACK_LABELS = {
  push: 'Push',
  pull: 'Pull',
  core: 'Core',
  legs: 'Legs',
}

const TRACK_COLORS = {
  push: '#f59e0b',
  pull: '#60a5fa',
  core: '#a78bfa',
  legs: '#34d399',
}

export default function TrackPage() {
  const { trackId } = useParams()
  const { user } = useAuth()

  const [skills, setSkills] = useState([])
  // prereqMap: { skillId: [requiredSkillId, ...] }
  // tells us what must be unlocked before each skill becomes available
  const [prereqMap, setPrereqMap] = useState({})
  // skillMap: { skillId: skill } — used to look up a skill's name by ID
  const [skillMap, setSkillMap] = useState({})
  const [unlockedIds, setUnlockedIds] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [selectedSkill, setSelectedSkill] = useState(null)

  const label = TRACK_LABELS[trackId]
  const color = TRACK_COLORS[trackId]

  // Re-fetch whenever the user navigates to a different track or logs in/out
  useEffect(() => {
    if (!label) return

    async function loadTrack() {
      setLoading(true)

      // Fetch all skills for this track, ordered by their position in the chain
      const { data: skillData, error: skillError } = await supabase
        .from('skills')
        .select('*')
        .eq('track', trackId)
        .order('order_in_track')

      if (skillError || !skillData) {
        setLoading(false)
        return
      }

      // Build a lookup map so we can find a skill's name from its ID
      const map = {}
      for (const skill of skillData) {
        map[skill.id] = skill
      }

      // Fetch the prerequisite relationships for all skills in this track
      const skillIds = skillData.map(s => s.id)
      const { data: prereqData } = await supabase
        .from('skill_prerequisites')
        .select('skill_id, requires_skill_id')
        .in('skill_id', skillIds)

      // Build prereqMap: { skillId: [requiredSkillId, ...] }
      const prereqs = {}
      for (const row of prereqData ?? []) {
        prereqs[row.skill_id] = prereqs[row.skill_id] ?? []
        prereqs[row.skill_id].push(row.requires_skill_id)
      }

      // Fetch the user's unlocked skills if they are logged in
      let unlocked = new Set()
      if (user) {
        const { data: userSkillData } = await supabase
          .from('user_skills')
          .select('skill_id')
          .eq('user_id', user.id)
          .eq('status', 'unlocked')
        unlocked = new Set((userSkillData ?? []).map(us => us.skill_id))
      }

      setSkills(skillData)
      setSkillMap(map)
      setPrereqMap(prereqs)
      setUnlockedIds(unlocked)
      setLoading(false)
    }

    loadTrack()
  }, [trackId, user, label])

  // Determine the display state for a single skill:
  // 'unlocked'   — user has unlocked it
  // 'unlockable' — all prerequisites are met (or there are none), so the user can attempt it
  // 'locked'     — at least one prerequisite is not yet unlocked
  function getSkillState(skill) {
    if (unlockedIds.has(skill.id)) return 'unlocked'
    const prereqs = prereqMap[skill.id] ?? []
    const allMet = prereqs.every(reqId => unlockedIds.has(reqId))
    return allMet ? 'unlockable' : 'locked'
  }

  // Group skills into tiers — skills sharing the same order_in_track value
  // sit side by side in the same row (this is how branches are displayed)
  function buildTiers() {
    const tiers = []
    const tierMap = new Map()
    for (const skill of skills) {
      if (!tierMap.has(skill.order_in_track)) {
        const tier = []
        tierMap.set(skill.order_in_track, tier)
        tiers.push(tier)
      }
      tierMap.get(skill.order_in_track).push(skill)
    }
    return tiers
  }

  // Renders the connector between a tier and the parent tier below it.
  // Single-node tier: a simple vertical line.
  // Multi-node tier: an H-shaped SVG — trunk rises from parent, horizontal bar
  // spans all nodes, drops connect the bar to each node above.
  function renderConnector(tier) {
    if (tier.length === 1) {
      return <div className={styles.connector} style={{ background: color }} />
    }

    // These must match SkillNode.module.css (.node width) and .tier gap (1rem = 16px)
    const NODE_WIDTH = 200
    const NODE_GAP = 16
    const svgWidth = tier.length * NODE_WIDTH + (tier.length - 1) * NODE_GAP
    const svgHeight = 48
    const midY = svgHeight / 2

    // x-centre of each node, left to right
    const nodeCenters = tier.map((_, i) => i * (NODE_WIDTH + NODE_GAP) + NODE_WIDTH / 2)
    const centerX = svgWidth / 2

    return (
      <svg width={svgWidth} height={svgHeight} style={{ display: 'block' }}>
        {/* Trunk: rises from the parent tier (bottom of SVG) to the horizontal bar */}
        <line x1={centerX} y1={svgHeight} x2={centerX} y2={midY} stroke={color} strokeWidth={2} />
        {/* Horizontal bar spanning all branch nodes */}
        <line x1={nodeCenters[0]} y1={midY} x2={nodeCenters[nodeCenters.length - 1]} y2={midY} stroke={color} strokeWidth={2} />
        {/* Short vertical drops from the bar up to each node */}
        {nodeCenters.map((cx, i) => (
          <line key={i} x1={cx} y1={midY} x2={cx} y2={0} stroke={color} strokeWidth={2} />
        ))}
      </svg>
    )
  }

  // For a locked skill, find the name of its first prerequisite to display
  // "Requires: X" on the card
  function getPrerequisiteName(skill) {
    const prereqs = prereqMap[skill.id] ?? []
    if (prereqs.length === 0) return null
    return skillMap[prereqs[0]]?.name ?? null
  }

  if (!label) {
    return (
      <main className={styles.container}>
        <p>Track not found.</p>
        <Link to="/skill-tree">← Back to skill tree</Link>
      </main>
    )
  }

  const tiers = buildTiers()

  return (
    <main className={styles.container}>
      <Link to="/skill-tree" className={styles.back}>← Skill tree</Link>

      <h1 className={styles.title} style={{ color }}>{label} Track</h1>
      <p className={styles.subtitle}>
        {loading ? 'Loading skills…' : `${skills.length} skill${skills.length !== 1 ? 's' : ''}`}
      </p>

      {!loading && (
        <div className={styles.chain}>
          {tiers.map((tier, tierIndex) => (
            <div key={tierIndex} className={styles.tierGroup}>
              {/* Connector between this tier and the parent tier below it */}
              {tierIndex > 0 && renderConnector(tier)}

              <div className={styles.tier}>
                {tier.map(skill => (
                  <SkillNode
                    key={skill.id}
                    skill={skill}
                    state={getSkillState(skill)}
                    trackColor={color}
                    prerequisiteName={getPrerequisiteName(skill)}
                    onClick={() => setSelectedSkill(skill)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <SkillModal
        skill={selectedSkill}
        trackColor={color}
        onClose={() => setSelectedSkill(null)}
      />
    </main>
  )
}
