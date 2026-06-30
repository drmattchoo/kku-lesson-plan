import { useEffect, useState } from 'react'
import './App.css'

const STAGES = [
  'อาจารย์ผู้สอน',
  'อัปโหลดเอกสารหลักสูตร',
  'เลือกหัวข้อบรรยาย',
  'แก้ไขแผนการสอน',
  'ดาวน์โหลด',
]

const EMPTY_PROFILE = { name: '', title: '' }

const SESSION_ID_KEY = 'lessonPlanSessionId'

function refsToList(text) {
  return text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

async function parseErrorOrThrow(resp) {
  if (resp.status === 401) {
    window.location.href = '/auth/login'
    throw new Error('redirecting to login')
  }
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new Error(body.detail || `เกิดข้อผิดพลาด (${resp.status})`)
  }
}

function BackButton({ onBack }) {
  if (!onBack) return null
  return (
    <button type="button" className="back-button" onClick={onBack}>
      ย้อนกลับ
    </button>
  )
}

function InstructorForm({ sessionId, initialProfile, onSaved, onBack }) {
  const [profile, setProfile] = useState(initialProfile)
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
      const url = sessionId ? `/api/session/${sessionId}` : '/api/session'
      const resp = await fetch(url, {
        method: sessionId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
        credentials: 'include',
      })
      await parseErrorOrThrow(resp)
      const data = await resp.json()
      onSaved(data.sessionId, profile)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="instructor-form" onSubmit={handleSubmit}>
      <h2>ข้อมูลอาจารย์ผู้สอน</h2>
      <p className="hint">ข้อมูลรายวิชาจะดึงจากเอกสารหลักสูตรที่อัปโหลดในขั้นตอนถัดไป</p>

      <label>
        ชื่อ-สกุล
        <input required value={profile.name} onChange={update('name')} />
      </label>
      <label>
        ตำแหน่ง
        <input required value={profile.title} onChange={update('title')} />
      </label>

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <BackButton onBack={onBack} />
        <button type="submit" disabled={submitting}>
          {submitting ? 'กำลังบันทึก…' : 'ถัดไป'}
        </button>
      </div>
    </form>
  )
}

function UploadForm({ sessionId, onExtracted, onBack }) {
  const [specFile, setSpecFile] = useState(null)
  const [slidesFile, setSlidesFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!specFile) return
    setSubmitting(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('sid', sessionId)
      formData.append('spec', specFile)
      if (slidesFile) formData.append('slides', slidesFile)

      const resp = await fetch('/api/extract', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      })
      await parseErrorOrThrow(resp)
      const course = await resp.json()
      onExtracted(course)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h2>อัปโหลดเอกสารหลักสูตร</h2>
      <p className="hint">
        เอกสารหลักสูตร/รายละเอียดรายวิชา (เช่น มคอ-3 หรือรูปแบบอื่นที่เทียบเท่า) เป็นไฟล์เดียวที่จำเป็น
        — สไลด์ประกอบการสอนเป็นตัวเลือกเสริม
      </p>

      <label>
        เอกสารหลักสูตร (จำเป็น)
        <input
          type="file"
          accept=".docx,.pptx"
          required
          onChange={(e) => setSpecFile(e.target.files[0] || null)}
        />
      </label>
      <label>
        สไลด์ประกอบการสอน (ไม่บังคับ)
        <input
          type="file"
          accept=".docx,.pptx"
          onChange={(e) => setSlidesFile(e.target.files[0] || null)}
        />
      </label>

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <BackButton onBack={onBack} />
        <button type="submit" disabled={submitting || !specFile}>
          {submitting ? 'กำลังประมวลผล…' : 'แยกข้อมูลรายวิชา'}
        </button>
      </div>
    </form>
  )
}

function CorrectionScreen({ sessionId, initialCourse, onLectureChosen, onBack }) {
  const [course, setCourse] = useState(initialCourse)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  function updateField(field, value) {
    setCourse({ ...course, [field]: value })
    setSaved(false)
  }

  function updateListItem(listName, index, field, value) {
    const list = course[listName].slice()
    list[index] = { ...list[index], [field]: value }
    setCourse({ ...course, [listName]: list })
    setSaved(false)
  }

  function updateLectureTopic(index, value) {
    const list = course.lectures.slice()
    list[index] = { ...list[index], topic: value, name: value }
    setCourse({ ...course, lectures: list })
    setSaved(false)
  }

  function addListItem(listName, empty) {
    setCourse({ ...course, [listName]: [...course[listName], empty] })
    setSaved(false)
  }

  function removeListItem(listName, index) {
    setCourse({ ...course, [listName]: course[listName].filter((_, i) => i !== index) })
    setSaved(false)
  }

  async function handleSave() {
    setSaving(true)
    setError('')
    try {
      const resp = await fetch(`/api/course/${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(course),
        credentials: 'include',
      })
      await parseErrorOrThrow(resp)
      const data = await resp.json()
      setCourse(data)
      setSaved(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="correction-screen">
      <h2>ตรวจสอบและแก้ไขข้อมูลรายวิชา</h2>
      <p className="hint">ข้อมูลที่ดึงมาเป็นแบบร่าง — กรุณาตรวจสอบและแก้ไขก่อนสร้างแผนการสอน</p>

      <label>
        รหัสวิชา
        <input value={course.courseCode} onChange={(e) => updateField('courseCode', e.target.value)} />
      </label>
      <label>
        ชื่อวิชา
        <input value={course.courseName} onChange={(e) => updateField('courseName', e.target.value)} />
      </label>
      <label>
        ปีการศึกษา
        <input value={course.academicYear} onChange={(e) => updateField('academicYear', e.target.value)} />
      </label>
      <label>
        ภาคการศึกษา
        <input value={course.semester} onChange={(e) => updateField('semester', e.target.value)} />
      </label>
      <label>
        สาขาวิชา/ภาควิชา
        <input value={course.department} onChange={(e) => updateField('department', e.target.value)} />
      </label>
      <label>
        คณะ
        <input value={course.faculty} onChange={(e) => updateField('faculty', e.target.value)} />
      </label>
      <label>
        มหาวิทยาลัย
        <input value={course.university} onChange={(e) => updateField('university', e.target.value)} />
      </label>
      <label>
        ผู้เรียน
        <input value={course.learners} onChange={(e) => updateField('learners', e.target.value)} />
      </label>

      <h3>PLO</h3>
      {course.PLOs.map((plo, i) => (
        <div className="row" key={i}>
          <input
            placeholder="id"
            className="col-id"
            value={plo.id}
            onChange={(e) => updateListItem('PLOs', i, 'id', e.target.value)}
          />
          <input
            placeholder="ข้อความ"
            value={plo.text}
            onChange={(e) => updateListItem('PLOs', i, 'text', e.target.value)}
          />
          <button type="button" onClick={() => removeListItem('PLOs', i)}>
            ลบ
          </button>
        </div>
      ))}
      <button type="button" onClick={() => addListItem('PLOs', { id: '', text: '' })}>
        + เพิ่ม PLO
      </button>

      <h3>CLO</h3>
      {course.CLOs.map((clo, i) => (
        <div className="row" key={i}>
          <input
            placeholder="id"
            className="col-id"
            value={clo.id}
            onChange={(e) => updateListItem('CLOs', i, 'id', e.target.value)}
          />
          <input
            placeholder="ข้อความ"
            value={clo.text}
            onChange={(e) => updateListItem('CLOs', i, 'text', e.target.value)}
          />
          <input
            placeholder="PLO ที่เกี่ยวข้อง (คั่นด้วย ,)"
            className="col-refs"
            value={clo.ploRefs.join(', ')}
            onChange={(e) => updateListItem('CLOs', i, 'ploRefs', refsToList(e.target.value))}
          />
          <button type="button" onClick={() => removeListItem('CLOs', i)}>
            ลบ
          </button>
        </div>
      ))}
      <button type="button" onClick={() => addListItem('CLOs', { id: '', text: '', ploRefs: [] })}>
        + เพิ่ม CLO
      </button>

      <h3>หัวข้อบรรยาย (เลือก 1 หัวข้อเพื่อสร้างแผนการสอน)</h3>
      {course.lectures.map((lec, i) => (
        <div className="row lecture-row" key={i}>
          <input
            placeholder="สัปดาห์"
            className="col-week"
            value={lec.week}
            onChange={(e) => updateListItem('lectures', i, 'week', e.target.value)}
          />
          <input
            placeholder="หัวข้อ"
            value={lec.topic}
            onChange={(e) => updateLectureTopic(i, e.target.value)}
          />
          <input
            type="number"
            placeholder="นาที"
            className="col-minutes"
            value={lec.durationMin ?? ''}
            onChange={(e) =>
              updateListItem('lectures', i, 'durationMin', e.target.value ? Number(e.target.value) : null)
            }
          />
          <input
            placeholder="CLO (คั่นด้วย ,)"
            className="col-refs"
            value={lec.cloRefs.join(', ')}
            onChange={(e) => updateListItem('lectures', i, 'cloRefs', refsToList(e.target.value))}
          />
          <button type="button" onClick={() => removeListItem('lectures', i)}>
            ลบ
          </button>
          <button type="button" className="choose-button" onClick={() => onLectureChosen(lec)} disabled={!saved}>
            เลือก
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() =>
          addListItem('lectures', {
            id: String(course.lectures.length + 1),
            week: '',
            topic: '',
            name: '',
            durationMin: null,
            cloRefs: [],
          })
        }
      >
        + เพิ่มหัวข้อ
      </button>

      {error && <p className="form-error">{error}</p>}
      <div className="form-actions">
        <BackButton onBack={onBack} />
        <button type="button" className="save-button" onClick={handleSave} disabled={saving}>
          {saving ? 'กำลังบันทึก…' : 'บันทึกการแก้ไข'}
        </button>
      </div>
      {saved && <p className="save-confirm">บันทึกแล้ว — กดปุ่ม "เลือก" ที่หัวข้อด้านบนเพื่อสร้างแผนการสอน</p>}
    </div>
  )
}

const TEACHING_METHODS = ['lecture', 'interactive', 'quiz']

function OutlineEditor({ sessionId, lecture, onSaved, onBack }) {
  const [brief, setBrief] = useState('')
  const [outline, setOutline] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savedTotal, setSavedTotal] = useState(null)
  const [error, setError] = useState('')

  const liveTotal = outline
    ? outline.keyPoints.reduce((sum, kp) => sum + (Number(kp.durationMin) || 0), 0)
    : 0

  async function handleGenerate() {
    setGenerating(true)
    setError('')
    try {
      const resp = await fetch('/api/outline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sid: sessionId, lectureId: lecture.id, brief: brief || null }),
        credentials: 'include',
      })
      await parseErrorOrThrow(resp)
      const data = await resp.json()
      setOutline(data)
      setSavedTotal(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  function updateKeyPoint(index, field, value) {
    const keyPoints = outline.keyPoints.slice()
    keyPoints[index] = { ...keyPoints[index], [field]: value }
    setOutline({ ...outline, keyPoints })
  }

  function moveKeyPoint(index, direction) {
    const keyPoints = outline.keyPoints.slice()
    const target = index + direction
    if (target < 0 || target >= keyPoints.length) return
    ;[keyPoints[index], keyPoints[target]] = [keyPoints[target], keyPoints[index]]
    keyPoints.forEach((kp, i) => (kp.seq = i + 1))
    setOutline({ ...outline, keyPoints })
  }

  function removeKeyPoint(index) {
    const keyPoints = outline.keyPoints.filter((_, i) => i !== index)
    keyPoints.forEach((kp, i) => (kp.seq = i + 1))
    setOutline({ ...outline, keyPoints })
  }

  function addKeyPoint() {
    const keyPoints = [
      ...outline.keyPoints,
      {
        seq: outline.keyPoints.length + 1,
        title: '',
        objective: '',
        content: '',
        durationMin: 10,
        teachingMethod: 'lecture',
        cloRefs: [],
        materials: '',
        assessment: '',
      },
    ]
    setOutline({ ...outline, keyPoints })
  }

  async function handleSave() {
    setSaving(true)
    setError('')
    try {
      const payload = { ...outline, totalDurationMin: liveTotal }
      const resp = await fetch(`/api/outline/${lecture.id}?sid=${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      })
      await parseErrorOrThrow(resp)
      const data = await resp.json()
      setSavedTotal(data.totalMin)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!outline) {
    return (
      <div className="outline-editor">
        <h2>สร้างแผนการสอน: {lecture.topic}</h2>
        <label>
          ข้อมูลเพิ่มเติม / ความตั้งใจของผู้สอน (ไม่บังคับ)
          <textarea value={brief} onChange={(e) => setBrief(e.target.value)} rows={3} />
        </label>
        {error && <p className="form-error">{error}</p>}
        <div className="form-actions">
          <BackButton onBack={onBack} />
          <button type="button" onClick={handleGenerate} disabled={generating}>
            {generating ? 'กำลังสร้าง…' : 'สร้างแผนการสอน'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="outline-editor">
      <h2>แก้ไขแผนการสอน: {lecture.topic}</h2>
      <p className="hint">
        เวลารวมปัจจุบัน: {liveTotal} นาที
        {lecture.durationMin ? ` (กำหนดไว้ ${lecture.durationMin} นาที)` : ''}
      </p>

      {outline.keyPoints.map((kp, i) => (
        <div className="keypoint-card" key={i}>
          <div className="keypoint-header">
            <strong>ลำดับที่ {kp.seq}</strong>
            <div className="keypoint-actions">
              <button type="button" onClick={() => moveKeyPoint(i, -1)} disabled={i === 0}>
                ▲
              </button>
              <button
                type="button"
                onClick={() => moveKeyPoint(i, 1)}
                disabled={i === outline.keyPoints.length - 1}
              >
                ▼
              </button>
              <button type="button" onClick={() => removeKeyPoint(i)}>
                ลบ
              </button>
            </div>
          </div>
          <label>
            หัวข้อ
            <input value={kp.title} onChange={(e) => updateKeyPoint(i, 'title', e.target.value)} />
          </label>
          <label>
            วัตถุประสงค์
            <input value={kp.objective} onChange={(e) => updateKeyPoint(i, 'objective', e.target.value)} />
          </label>
          <label>
            เนื้อหา
            <textarea rows={2} value={kp.content} onChange={(e) => updateKeyPoint(i, 'content', e.target.value)} />
          </label>
          <div className="row">
            <label className="col-minutes">
              นาที
              <input
                type="number"
                value={kp.durationMin}
                onChange={(e) => updateKeyPoint(i, 'durationMin', Number(e.target.value))}
              />
            </label>
            <label>
              กิจกรรม
              <select
                value={kp.teachingMethod}
                onChange={(e) => updateKeyPoint(i, 'teachingMethod', e.target.value)}
              >
                {TEACHING_METHODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
            <label className="col-refs">
              CLO
              <input
                value={kp.cloRefs.join(', ')}
                onChange={(e) => updateKeyPoint(i, 'cloRefs', refsToList(e.target.value))}
              />
            </label>
          </div>
          <label>
            สื่อการสอน
            <input value={kp.materials} onChange={(e) => updateKeyPoint(i, 'materials', e.target.value)} />
          </label>
          <label>
            การประเมินผล
            <input value={kp.assessment} onChange={(e) => updateKeyPoint(i, 'assessment', e.target.value)} />
          </label>
        </div>
      ))}

      <button type="button" onClick={addKeyPoint}>
        + เพิ่มหัวข้อย่อย
      </button>

      {error && <p className="form-error">{error}</p>}
      <div className="form-actions">
        <BackButton onBack={onBack} />
        <button type="button" className="save-button" onClick={handleSave} disabled={saving}>
          {saving ? 'กำลังบันทึก…' : 'บันทึกแผนการสอน'}
        </button>
      </div>
      {savedTotal != null && (
        <div className="save-confirm">
          <p>บันทึกแล้ว — เวลารวม {savedTotal} นาที</p>
          <button type="button" className="choose-button" onClick={onSaved}>
            ถัดไป: ดาวน์โหลด
          </button>
        </div>
      )}
    </div>
  )
}

async function downloadBlob(resp, filename) {
  await parseErrorOrThrow(resp)
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function ExportScreen({ sessionId, lecture, completedLectureIds, onPickAnother, onBack }) {
  const [sessionDate, setSessionDate] = useState('')
  const [sessionTime, setSessionTime] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')

  async function handleDownloadOne() {
    setDownloading(true)
    setError('')
    try {
      const resp = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sid: sessionId, lectureId: lecture.id, sessionDate, sessionTime }),
        credentials: 'include',
      })
      await downloadBlob(resp, `lesson_plan_${lecture.id}.docx`)
    } catch (err) {
      setError(err.message)
    } finally {
      setDownloading(false)
    }
  }

  async function handleDownloadBatch() {
    setDownloading(true)
    setError('')
    try {
      const resp = await fetch('/api/export/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sid: sessionId, lectureIds: completedLectureIds, sessionDate, sessionTime }),
        credentials: 'include',
      })
      await downloadBlob(resp, 'lesson_plans.zip')
    } catch (err) {
      setError(err.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="export-screen">
      <h2>ดาวน์โหลดแผนการสอน: {lecture.topic}</h2>

      <label>
        วันที่สอน
        <input value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} placeholder="เช่น 1 กรกฎาคม 2569" />
      </label>
      <label>
        เวลาสอน
        <input value={sessionTime} onChange={(e) => setSessionTime(e.target.value)} placeholder="เช่น 09:00-10:00" />
      </label>

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <BackButton onBack={onBack} />
        <button type="button" onClick={handleDownloadOne} disabled={downloading}>
          {downloading ? 'กำลังสร้างไฟล์…' : 'ดาวน์โหลด .docx (หัวข้อนี้)'}
        </button>
      </div>

      {completedLectureIds.length > 1 && (
        <button type="button" onClick={handleDownloadBatch} disabled={downloading}>
          ดาวน์โหลดทั้งหมด ({completedLectureIds.length} หัวข้อ) เป็น .zip
        </button>
      )}

      <button type="button" className="secondary-button" onClick={onPickAnother}>
        + เพิ่มแผนการสอนสำหรับหัวข้ออื่น
      </button>
    </div>
  )
}

function App() {
  const [stage, setStage] = useState(0)
  const [maxStage, setMaxStage] = useState(0)
  const [sessionId, setSessionId] = useState(null)
  const [profile, setProfile] = useState(EMPTY_PROFILE)
  const [course, setCourse] = useState(null)
  const [selectedLecture, setSelectedLecture] = useState(null)
  const [completedLectureIds, setCompletedLectureIds] = useState([])
  const [resuming, setResuming] = useState(true)

  function goToStage(target) {
    setStage(target)
    setMaxStage((m) => Math.max(m, target))
  }

  useEffect(() => {
    const savedId = localStorage.getItem(SESSION_ID_KEY)
    if (!savedId) {
      setResuming(false)
      return
    }
    fetch(`/api/session/${savedId}`, { credentials: 'include' })
      .then((resp) => {
        if (!resp.ok) {
          localStorage.removeItem(SESSION_ID_KEY)
          return null
        }
        return resp.json()
      })
      .then((data) => {
        if (!data) return
        setSessionId(savedId)
        if (data.instructorProfile) setProfile(data.instructorProfile)
        if (data.course) {
          setCourse(data.course)
          setCompletedLectureIds(data.outlineLectureIds || [])
          goToStage(2)
        } else if (data.instructorProfile) {
          goToStage(1)
        }
      })
      .catch(() => localStorage.removeItem(SESSION_ID_KEY))
      .finally(() => setResuming(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleProfileSaved(newSessionId, savedProfile) {
    localStorage.setItem(SESSION_ID_KEY, newSessionId)
    setSessionId(newSessionId)
    setProfile(savedProfile)
    goToStage(1)
  }

  function handleExtracted(extractedCourse) {
    setCourse(extractedCourse)
    goToStage(2)
  }

  function handleLectureChosen(lecture) {
    setSelectedLecture(lecture)
    goToStage(3)
  }

  function handleOutlineSaved() {
    setCompletedLectureIds((ids) =>
      ids.includes(selectedLecture.id) ? ids : [...ids, selectedLecture.id]
    )
    goToStage(4)
  }

  if (resuming) {
    return (
      <div className="wizard">
        <p className="hint">กำลังโหลด…</p>
      </div>
    )
  }

  return (
    <div className="wizard">
      <header>
        <h1>แผนการสอน Generator</h1>
        <ol className="stage-tracker">
          {STAGES.map((label, i) => (
            <li
              key={label}
              className={[
                i === stage ? 'active' : i < stage ? 'done' : '',
                i <= maxStage ? 'clickable' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              onClick={() => i <= maxStage && setStage(i)}
            >
              {label}
            </li>
          ))}
        </ol>
      </header>

      <main>
        {stage === 0 && (
          <InstructorForm
            sessionId={sessionId}
            initialProfile={profile}
            onSaved={handleProfileSaved}
          />
        )}
        {stage === 1 && (
          <UploadForm
            sessionId={sessionId}
            onExtracted={handleExtracted}
            onBack={() => setStage(0)}
          />
        )}
        {stage === 2 && course && (
          <CorrectionScreen
            sessionId={sessionId}
            initialCourse={course}
            onLectureChosen={handleLectureChosen}
            onBack={() => setStage(1)}
          />
        )}
        {stage === 3 && selectedLecture && (
          <OutlineEditor
            sessionId={sessionId}
            lecture={selectedLecture}
            onSaved={handleOutlineSaved}
            onBack={() => setStage(2)}
          />
        )}
        {stage === 4 && selectedLecture && (
          <ExportScreen
            sessionId={sessionId}
            lecture={selectedLecture}
            completedLectureIds={completedLectureIds}
            onPickAnother={() => setStage(2)}
            onBack={() => setStage(3)}
          />
        )}
      </main>
    </div>
  )
}

export default App
