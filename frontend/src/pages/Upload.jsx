import styles from "./Upload.module.css";
import { useState } from "react"

export default function Upload() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [filename, setFilename] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    const formData = new FormData()
    formData.append("file", selectedFile)
    const response = await fetch("http://127.0.0.1:8000/upload", {
      method: "POST",
      body: formData
    })
    const data = await response.json()
    setFilename(data.filename)
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
          <input type="file" name="file" accept="video/*" onChange={(e) => setSelectedFile(e.target.files[0])}/>
          <button type="submit">Upload</button>
          {filename && <p>Uploaded: {filename}</p>}
        </form>
      </div>
    </main>
  );
}
