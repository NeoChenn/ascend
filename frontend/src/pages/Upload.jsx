import styles from "./Upload.module.css";
import { useState } from "react"

export default function Upload() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [exercise, setExercise] = useState("pull_up")
  const [filename, setFilename] = useState("")
  const [feedback, setFeedback] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const formData = new FormData()
    formData.append("file", selectedFile)
    formData.append("exercise", exercise)
    const response = await fetch("http://127.0.0.1:8000/upload", {
      method: "POST",
      body: formData
    })
    const data = await response.json()
    setFilename(data.filename)
    setFeedback(data.feedback)
  }

  return (
    <main className={styles.container}>
      <h1>Upload a video</h1>
      <p className={styles.subtitle}>
        Record yourself performing a pull-up or push-up and upload it here for
        form analysis.
      </p>
      <div className={styles.dropzone}>
        <form onSubmit={handleSubmit}>
          <select value={exercise} onChange={(e) => setExercise(e.target.value)}>
            <option value="pull_up">Pull-up</option>
            <option value="push_up">Push-up</option>
          </select>
          <input type="file" name="file" accept="video/*" onChange={(e) => setSelectedFile(e.target.files[0])}/>
          <button type="submit">Upload</button>
          {filename && <p>Uploaded: {filename}</p>}
        </form>
      </div>

      {feedback && (
        <div className={styles.feedback}>
          <h2>Form Feedback</h2>
          <p className={styles.repCount}>
            {feedback.rep_count} rep{feedback.rep_count !== 1 ? "s" : ""} detected
          </p>
          <ul className={styles.checkList}>
            {feedback.checks.map((check) => (
              <li
                key={check.name}
                className={check.passed ? styles.checkPass : styles.checkFail}
              >
                <span className={styles.checkIcon}>{check.passed ? "✓" : "✗"}</span>
                <span>{check.message}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}
