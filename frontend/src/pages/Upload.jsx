import styles from './Upload.module.css'

export default function Upload() {
  return (
    <main className={styles.container}>
      <h1>Upload a video</h1>
      <p className={styles.subtitle}>Record yourself performing a pull-up or push-up and upload it here for form analysis.</p>
      <div className={styles.dropzone}>
        <p>Video upload coming soon</p>
      </div>
    </main>
  )
}
