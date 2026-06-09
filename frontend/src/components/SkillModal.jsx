import { useState, useRef, useEffect } from 'react'
import styles from './SkillModal.module.css'

// Joint pairs to draw as lines. Only the 10 joints the backend extracts are used.
const SKELETON_CONNECTIONS = [
  ['left_shoulder',  'left_elbow'],
  ['left_elbow',     'left_wrist'],
  ['right_shoulder', 'right_elbow'],
  ['right_elbow',    'right_wrist'],
  ['left_shoulder',  'right_shoulder'],
  ['left_shoulder',  'left_hip'],
  ['right_shoulder', 'right_hip'],
  ['left_hip',       'right_hip'],
  ['left_hip',       'left_knee'],
  ['right_hip',      'right_knee'],
]

// Draws one frame of landmarks onto a canvas.
// Landmarks are normalised 0–1 coordinates, so we multiply by canvas width/height.
// Joints with visibility < 0.5 are skipped — MediaPipe wasn't confident about those.
function drawSkeleton(canvas, landmarks) {
  const ctx = canvas.getContext('2d')
  const { width, height } = canvas
  ctx.clearRect(0, 0, width, height)

  ctx.strokeStyle = '#00e5ff'
  ctx.lineWidth = 2
  for (const [nameA, nameB] of SKELETON_CONNECTIONS) {
    const a = landmarks[nameA]
    const b = landmarks[nameB]
    if (!a || !b || a.visibility < 0.5 || b.visibility < 0.5) continue
    ctx.beginPath()
    ctx.moveTo(a.x * width, a.y * height)
    ctx.lineTo(b.x * width, b.y * height)
    ctx.stroke()
  }

  for (const lm of Object.values(landmarks)) {
    if (lm.visibility < 0.5) continue
    ctx.beginPath()
    ctx.arc(lm.x * width, lm.y * height, 4, 0, Math.PI * 2)
    ctx.fillStyle = '#ffffff'
    ctx.fill()
    ctx.strokeStyle = '#00e5ff'
    ctx.lineWidth = 1.5
    ctx.stroke()
  }
}

// Modal for a skill node. Handles three cases:
//   locked     → shows skill info + demo video (if any) + disabled "Locked" button
//   unlockable → shows skill info + demo video (if any) + filming instructions + upload button
//   unlocked   → shows skill info + user's own unlock video + filming instructions + upload button
//
// Props:
//   skill              — full skill row from Supabase
//   skillState         — 'locked' | 'unlockable' | 'unlocked'
//   trackColor         — hex colour string for this track
//   unlockVideoUrl     — the user's own stored video URL (unlocked state only)
//   onClose            — called when the user dismisses the modal
//   onAttemptComplete  — (skillId, passed, feedbackChecks, videoFile)
export default function SkillModal({ skill, skillState, trackColor, user, unlockVideoUrl, onClose, onAttemptComplete }) {
  const [uploadState, setUploadState] = useState('idle')  // 'idle' | 'uploading' | 'result' | 'error'
  const [result, setResult] = useState(null)              // { passed, checks, repCount, landmarks }
  const [videoPreviewUrl, setVideoPreviewUrl] = useState(null)

  const fileInputRef = useRef(null)
  const videoRef     = useRef(null)
  const canvasRef    = useRef(null)
  const animFrameRef = useRef(null)

  // Reset state when a different skill is opened without closing the modal first
  useEffect(() => {
    setUploadState('idle')
    setResult(null)
  }, [skill?.id])

  // Revoke the blob URL when it changes or the component unmounts, to free browser memory
  useEffect(() => {
    return () => {
      if (videoPreviewUrl) URL.revokeObjectURL(videoPreviewUrl)
    }
  }, [videoPreviewUrl])

  // Skeleton draw loop — active only in result state when landmark data exists.
  // requestAnimationFrame runs at the display refresh rate (~60fps), so the skeleton
  // stays in sync with the video as the user scrubs or plays it.
  useEffect(() => {
    if (uploadState !== 'result' || !result?.landmarks?.length) return

    function drawLoop() {
      const video  = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas) return

      // Keep canvas intrinsic size matching the video's rendered pixel size.
      // Without this, the canvas would use its default 300×150 and landmarks
      // would be drawn at the wrong scale.
      const rect = video.getBoundingClientRect()
      if (canvas.width !== rect.width || canvas.height !== rect.height) {
        canvas.width  = rect.width
        canvas.height = rect.height
      }

      // Map current video time → landmark frame index.
      // The backend extracts one entry per detected frame, so we spread them
      // evenly across the video's total duration.
      const frameIndex = Math.min(
        Math.floor((video.currentTime / (video.duration || 1)) * result.landmarks.length),
        result.landmarks.length - 1
      )
      drawSkeleton(canvas, result.landmarks[frameIndex])

      animFrameRef.current = requestAnimationFrame(drawLoop)
    }

    animFrameRef.current = requestAnimationFrame(drawLoop)
    return () => cancelAnimationFrame(animFrameRef.current)
  }, [uploadState, result])

  if (!skill) return null

  function handleBackdropClick(event) {
    if (uploadState === 'uploading') return
    if (event.target === event.currentTarget) onClose()
  }

  function handleFileSelect(event) {
    const file = event.target.files[0]
    if (file) handleUpload(file)
  }

  async function handleUpload(file) {
    setVideoPreviewUrl(URL.createObjectURL(file))
    setUploadState('uploading')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('exercise', skill.analysis_key)

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const data = await response.json()
      const checks = data.feedback.checks

      const threshold = skill.pass_threshold ?? 1.0
      const passed = checks.length > 0
        ? checks.filter(c => c.passed).length / checks.length >= threshold
        : false

      setResult({
        passed,
        checks,
        repCount:  data.feedback.rep_count,
        narrative: data.narrative ?? null,     // LLM coaching paragraph; null if API failed
        landmarks: data.landmarks_per_frame,   // used by the skeleton draw loop
      })
      setUploadState('result')
      onAttemptComplete(skill.id, passed, checks, file)
    } catch (err) {
      console.error('Upload failed:', err)
      setUploadState('error')
    }
  }

  const canUpload = !!skill.analysis_key

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.card}>

        <button
          className={styles.closeButton}
          onClick={onClose}
          disabled={uploadState === 'uploading'}
          aria-label="Close"
        >
          ×
        </button>

        <h2 className={styles.title} style={{ color: trackColor }}>
          {skill.name}
        </h2>

        {skill.description && (
          <p className={styles.description}>{skill.description}</p>
        )}

        {/* ── Uploading: plain video preview + pulsing text ── */}
        {uploadState === 'uploading' && (
          <div className={styles.previewSection}>
            <video className={styles.videoPreview} src={videoPreviewUrl} controls muted />
            <p className={styles.analysingText}>Analysing your attempt…</p>
          </div>
        )}

        {/* ── Result: skeleton overlay + verdict + feedback cards ── */}
        {uploadState === 'result' && result && (
          <div className={styles.resultSection}>

            {/* videoWrapper gives the canvas a positioned ancestor to anchor against */}
            <div className={styles.videoWrapper}>
              <video
                ref={videoRef}
                className={styles.videoPreview}
                src={videoPreviewUrl}
                controls
                loop
              />
              {/* Canvas sits on top of the video; pointer-events: none lets clicks
                  pass through to the video controls underneath */}
              <canvas ref={canvasRef} className={styles.skeletonCanvas} />
            </div>

            <div className={result.passed ? styles.verdictPass : styles.verdictFail}>
              {result.passed ? '✓ Skill unlocked!' : '✗ Not quite — keep training'}
            </div>
            <p className={styles.repCount}>
              {result.repCount} rep{result.repCount !== 1 ? 's' : ''} detected
            </p>

            {/* LLM coaching paragraph — omitted if the Gemini API call failed */}
            {result.narrative && (
              <p className={styles.narrative}>{result.narrative}</p>
            )}

            <ul className={styles.checkList}>
              {result.checks.map(check => (
                <li
                  key={check.name}
                  className={check.passed ? styles.checkPass : styles.checkFail}
                >
                  <span className={styles.checkIcon}>{check.passed ? '✓' : '✗'}</span>
                  <span>{check.message}</span>
                </li>
              ))}
            </ul>
            {!result.passed && (
              <button className={styles.retryButton} onClick={() => setUploadState('idle')}>
                Try again
              </button>
            )}
          </div>
        )}

        {/* ── Error ── */}
        {uploadState === 'error' && (
          <div className={styles.errorSection}>
            <p>Something went wrong. Please try again.</p>
            <button className={styles.retryButton} onClick={() => setUploadState('idle')}>
              Try again
            </button>
          </div>
        )}

        {/* ── Idle: video preview + (optionally) filming instructions + action button ── */}
        {uploadState === 'idle' && (
          <>
            {/* Unlocked: show the user's own stored video */}
            {skillState === 'unlocked' && unlockVideoUrl && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Your unlock attempt</h3>
                <video
                  src={unlockVideoUrl}
                  controls
                  className={styles.videoPreview}
                  style={{ marginBottom: 0 }}
                />
              </div>
            )}

            {/* Locked / unlockable: show the developer demo video if one exists */}
            {skillState !== 'unlocked' && skill.demo_video_url && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Demo</h3>
                <video
                  src={skill.demo_video_url}
                  controls
                  className={styles.videoPreview}
                  style={{ marginBottom: 0 }}
                />
              </div>
            )}

            {/* Filming instructions only shown when the user can actually attempt */}
            {skillState !== 'locked' && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Filming instructions</h3>
                <p className={styles.instructions}>
                  {skill.filming_instructions ?? 'Film from the side, full body in frame.'}
                </p>
              </div>
            )}

            <input
              type="file"
              accept="video/*"
              ref={fileInputRef}
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {/* Locked: show a disabled button — no upload possible until prerequisites are met */}
            {skillState === 'locked' ? (
              <button className={styles.uploadButton} disabled>
                Locked
              </button>
            ) : (
              <>
                {/* Warn unauthenticated users — upload still works but nothing is saved */}
                {!user && canUpload && (
                  <div className={styles.authBanner}>
                    <a href="/login">Sign in</a> to save your progress.
                  </div>
                )}
                <button
                  className={styles.uploadButton}
                  style={{ backgroundColor: canUpload ? trackColor : undefined }}
                  disabled={!canUpload}
                  onClick={() => fileInputRef.current.click()}
                >
                  {canUpload ? 'Upload attempt' : 'Coming soon'}
                </button>
              </>
            )}
          </>
        )}

      </div>
    </div>
  )
}
