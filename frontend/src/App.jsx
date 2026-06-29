import { useState } from 'react'
import './App.css'

const STAGES = [
  'อาจารย์ผู้สอน',
  'อัปโหลด มคอ-3',
  'เลือกหัวข้อบรรยาย',
  'แก้ไขแผนการสอน',
  'ดาวน์โหลด',
]

const EMPTY_PROFILE = {
  name: '',
  title: '',
  department: '',
  faculty: '',
  university: 'มหาวิทยาลัยขอนแก่น',
  courseCode: '',
  courseName: '',
  academicYear: '',
  semester: '',
  section: '',
}

function InstructorForm({ onCreated }) {
  const [profile, setProfile] = useState(EMPTY_PROFILE)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  function update(field) {
    return (e) => setProfile({ ...profile, [field]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const resp = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
        credentials: 'include',
      })
      if (resp.status === 401) {
        window.location.href = '/auth/login'
        return
      }
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}))
        throw new Error(body.detail || `เกิดข้อผิดพลาด (${resp.status})`)
      }
      const data = await resp.json()
      onCreated(data.sessionId, profile)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="instructor-form" onSubmit={handleSubmit}>
      <h2>ข้อมูลอาจารย์ผู้สอนและรายวิชา</h2>

      <label>
        ชื่อ-สกุล
        <input required value={profile.name} onChange={update('name')} />
      </label>
      <label>
        ตำแหน่ง
        <input required value={profile.title} onChange={update('title')} />
      </label>
      <label>
        สาขาวิชา/ภาควิชา
        <input required value={profile.department} onChange={update('department')} />
      </label>
      <label>
        คณะ
        <input required value={profile.faculty} onChange={update('faculty')} />
      </label>
      <label>
        มหาวิทยาลัย
        <input required value={profile.university} onChange={update('university')} />
      </label>
      <label>
        รหัสวิชา
        <input required value={profile.courseCode} onChange={update('courseCode')} />
      </label>
      <label>
        ชื่อวิชา
        <input required value={profile.courseName} onChange={update('courseName')} />
      </label>
      <label>
        ปีการศึกษา
        <input required value={profile.academicYear} onChange={update('academicYear')} />
      </label>
      <label>
        ภาคการศึกษา
        <input required value={profile.semester} onChange={update('semester')} />
      </label>
      <label>
        กลุ่มเรียน (ถ้ามี)
        <input value={profile.section} onChange={update('section')} />
      </label>

      {error && <p className="form-error">{error}</p>}

      <button type="submit" disabled={submitting}>
        {submitting ? 'กำลังบันทึก…' : 'ถัดไป'}
      </button>
    </form>
  )
}

function ComingSoon({ stageIndex }) {
  return (
    <div className="coming-soon">
      <h2>{STAGES[stageIndex]}</h2>
      <p>ขั้นตอนนี้ยังอยู่ระหว่างการพัฒนา (M7-M10)</p>
    </div>
  )
}

function App() {
  const [stage, setStage] = useState(0)
  const [sessionId, setSessionId] = useState(null)

  function handleCreated(newSessionId) {
    setSessionId(newSessionId)
    setStage(1)
  }

  return (
    <div className="wizard">
      <header>
        <h1>แผนการสอน Generator</h1>
        <ol className="stage-tracker">
          {STAGES.map((label, i) => (
            <li key={label} className={i === stage ? 'active' : i < stage ? 'done' : ''}>
              {label}
            </li>
          ))}
        </ol>
      </header>

      <main>
        {stage === 0 && <InstructorForm onCreated={handleCreated} />}
        {stage > 0 && (
          <>
            <p className="session-id">Session: {sessionId}</p>
            <ComingSoon stageIndex={stage} />
          </>
        )}
      </main>
    </div>
  )
}

export default App
