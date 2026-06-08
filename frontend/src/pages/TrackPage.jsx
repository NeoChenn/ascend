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
  const [prereqMap, setPrereqMap] = useState({})
  // skillMap: { skillId: skill } — used to look up a skill by ID
  const [skillMap, setSkillMap] = useState({})
  const [unlockedIds, setUnlockedIds] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [selectedSkill, setSelectedSkill] = useState(null)

  const label = TRACK_LABELS[trackId]
  const color = TRACK_COLORS[trackId]

  useEffect(() => {
    if (!label) return

    async function loadTrack() {
      setLoading(true)

      const { data: skillData, error: skillError } = await supabase
        .from('skills')
        .select('*')
        .eq('track', trackId)
        .order('order_in_track')

      if (skillError || !skillData) {
        setLoading(false)
        return
      }

      const map = {}
      for (const skill of skillData) {
        map[skill.id] = skill
      }

      const skillIds = skillData.map(s => s.id)
      const { data: prereqData } = await supabase
        .from('skill_prerequisites')
        .select('skill_id, requires_skill_id')
        .in('skill_id', skillIds)

      const prereqs = {}
      for (const row of prereqData ?? []) {
        prereqs[row.skill_id] = prereqs[row.skill_id] ?? []
        prereqs[row.skill_id].push(row.requires_skill_id)
      }

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

  function getSkillState(skill) {
    if (unlockedIds.has(skill.id)) return 'unlocked'
    const prereqs = prereqMap[skill.id] ?? []
    const allMet = prereqs.every(reqId => unlockedIds.has(reqId))
    return allMet ? 'unlockable' : 'locked'
  }

  function getPrerequisiteName(skill) {
    const prereqs = prereqMap[skill.id] ?? []
    if (prereqs.length === 0) return null
    return skillMap[prereqs[0]]?.name ?? null
  }

  // Analyse the tree and return a layout description.
  //
  // Walks upward from the root, following single-child links, until it finds the
  // "branch node" — the first skill with more than one in-track child (where the
  // tree fans out into independent columns). Chains are built only from the branch
  // node's direct children upward to their leaves, so shared ancestors like
  // "Explosive Pull-up" appear exactly once rather than once per leaf.
  //
  // Returns:
  //   branchNode  — the skill where the tree fans out (null if linear track)
  //   chains      — one array per column: [leaf, ..., direct child of branchNode]
  //   linearBase  — skills below the branch, in DOM order top→bottom:
  //                   • branched: [skill just below branchNode, ..., root]
  //                   • linear:   [leaf, ..., root]
  function buildLayout() {
    if (skills.length === 0) return { branchNode: null, chains: [], linearBase: [] }

    const trackSkillIds = new Set(skills.map(s => s.id))

    // childrenMap: parentId → [childId, ...] (in-track only)
    const childrenMap = {}
    for (const skill of skills) {
      const inTrackPrereqs = (prereqMap[skill.id] ?? []).filter(p => trackSkillIds.has(p))
      for (const parentId of inTrackPrereqs) {
        childrenMap[parentId] = childrenMap[parentId] ?? []
        childrenMap[parentId].push(skill.id)
      }
    }

    // Root: skill with no in-track prerequisites
    const root = skills.find(s =>
      ((prereqMap[s.id] ?? []).filter(p => trackSkillIds.has(p))).length === 0
    ) ?? null

    if (!root) return { branchNode: null, chains: [], linearBase: [] }

    // Walk from root following single-child links until we reach a branch or leaf.
    // linearBaseWalk collects skills in root-first order.
    const linearBaseWalk = []
    let branchNode = null
    let current = root

    while (true) {
      const children = childrenMap[current.id] ?? []
      if (children.length > 1) {
        // This node fans out — it is the branch node
        branchNode = current
        break
      } else if (children.length === 1) {
        linearBaseWalk.push(current)
        current = skillMap[children[0]]
      } else {
        // Leaf reached with no branching — purely linear track
        linearBaseWalk.push(current)
        break
      }
    }

    // Linear track: no branching at all
    if (!branchNode) {
      // Reverse so the leaf is first in DOM (renders at visual top)
      return { branchNode: null, chains: [], linearBase: [...linearBaseWalk].reverse() }
    }

    // Build one chain per child of the branch node.
    // Each chain is traced forward (child → leaf) then reversed so the leaf is at
    // the top of the column in the DOM.
    const chainChildren = childrenMap[branchNode.id] ?? []
    const chainsForward = chainChildren.map(childId => {
      const chain = []
      let c = skillMap[childId]
      while (c) {
        chain.push(c)
        const cChildren = childrenMap[c.id] ?? []
        // Follow single-child links; stop at a leaf or a nested branch (rare)
        c = cChildren.length === 1 ? skillMap[cChildren[0]] : null
      }
      return chain // [branchNode's child, ..., leaf]
    })

    // Sort chains left-to-right by the order_in_track of the branchNode's direct child
    chainsForward.sort((a, b) => (a[0]?.order_in_track ?? 0) - (b[0]?.order_in_track ?? 0))

    // Reverse each chain: leaf first in DOM (top of column), branchNode's child last (bottom)
    const chains = chainsForward.map(c => [...c].reverse())

    // linearBase for the branched case: skills between root (inclusive) and branchNode (exclusive),
    // reversed so the skill closest to branchNode is first in DOM (just below branchNode visually)
    const linearBase = [...linearBaseWalk].reverse()

    return { branchNode, chains, linearBase }
  }

  // Renders the connector between the branch node and the column bases.
  // Single column: a plain vertical line div (reuses .connector).
  // Multiple columns: H-shaped SVG — trunk from branchNode up to horizontal bar, drops to each column.
  //
  // NODE_WIDTH and NODE_GAP must match .column { width } and .columnsWrapper { gap } in CSS.
  function renderBranchSVG(columnCount) {
    if (columnCount === 1) {
      return <div className={styles.connector} style={{ background: color }} />
    }

    const NODE_WIDTH = 200
    const NODE_GAP = 16
    const svgWidth = columnCount * NODE_WIDTH + (columnCount - 1) * NODE_GAP
    const svgHeight = 48
    const midY = svgHeight / 2

    const columnCenters = Array.from({ length: columnCount }, (_, i) =>
      i * (NODE_WIDTH + NODE_GAP) + NODE_WIDTH / 2
    )
    const centerX = svgWidth / 2

    return (
      <svg width={svgWidth} height={svgHeight} style={{ display: 'block' }}>
        {/* Trunk: from the branch node (bottom of SVG) up to the horizontal bar */}
        <line x1={centerX} y1={svgHeight} x2={centerX} y2={midY} stroke={color} strokeWidth={2} />
        {/* Horizontal bar spanning all columns */}
        <line x1={columnCenters[0]} y1={midY} x2={columnCenters[columnCenters.length - 1]} y2={midY} stroke={color} strokeWidth={2} />
        {/* Drops from the bar up into each column */}
        {columnCenters.map((cx, i) => (
          <line key={i} x1={cx} y1={midY} x2={cx} y2={0} stroke={color} strokeWidth={2} />
        ))}
      </svg>
    )
  }

  function renderSkillNode(skill) {
    return (
      <SkillNode
        key={skill.id}
        skill={skill}
        state={getSkillState(skill)}
        trackColor={color}
        prerequisiteName={getPrerequisiteName(skill)}
        onClick={() => setSelectedSkill(skill)}
      />
    )
  }

  if (!label) {
    return (
      <main className={styles.container}>
        <p>Track not found.</p>
        <Link to="/skill-tree">← Back to skill tree</Link>
      </main>
    )
  }

  const { branchNode, chains, linearBase } = buildLayout()

  return (
    <main className={styles.container}>
      <Link to="/skill-tree" className={styles.back}>← Skill tree</Link>

      <h1 className={styles.title} style={{ color }}>{label} Track</h1>
      <p className={styles.subtitle}>
        {loading ? 'Loading skills…' : `${skills.length} skill${skills.length !== 1 ? 's' : ''}`}
      </p>

      {!loading && (
        <div className={styles.chain}>

          {/* Branching section: one vertical column per independent branch */}
          {chains.length > 0 && (
            <div className={styles.columnsWrapper}>
              {chains.map((chain, colIdx) => (
                <div key={colIdx} className={styles.column}>
                  {/*
                    flatMap so connectors are direct flex children of .column —
                    this ensures align-items: center actually centers the 2px line
                    on the node rather than left-aligning it inside a wrapper div
                  */}
                  {chain.flatMap((skill, skillIdx) => {
                    const items = [renderSkillNode(skill)]
                    if (skillIdx < chain.length - 1) {
                      items.push(
                        <div key={`conn-${skill.id}`} className={styles.connector} style={{ background: color }} />
                      )
                    }
                    return items
                  })}
                </div>
              ))}
            </div>
          )}

          {/* H-branch SVG (or single connector) connecting branch node to column bases */}
          {chains.length > 0 && renderBranchSVG(chains.length)}

          {/* Branch node: the skill where the tree fans out (rendered once, not in any column) */}
          {branchNode && renderSkillNode(branchNode)}

          {/* Linear base: skills at the bottom of the tree (below the branch node, or the whole
              tree if there is no branching). Each skill is preceded by a connector. */}
          {linearBase.flatMap((skill, i) => {
            const items = []
            // For a branched tree the first connector goes between branchNode and linearBase[0].
            // For a linear tree there is no branchNode, so skip the connector before the top skill.
            if (branchNode || i > 0) {
              items.push(
                <div key={`base-conn-${skill.id}`} className={styles.connector} style={{ background: color }} />
              )
            }
            items.push(renderSkillNode(skill))
            return items
          })}

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
