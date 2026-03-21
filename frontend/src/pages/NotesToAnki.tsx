import { useState, useRef, useCallback } from 'react'
import './NotesToAnki.css'

const API_URL = import.meta.env.VITE_API_URL || ''

interface Card {
  front: string
  back: string
  tags: string[]
  images: string[]
}

type AppState = 'idle' | 'uploading' | 'preview' | 'generating'

export default function NotesToAnki() {
  const [state, setState] = useState<AppState>('idle')
  const [cards, setCards] = useState<Card[]>([])
  const [deckName, setDeckName] = useState('My Deck')
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [editingIdx, setEditingIdx] = useState<number | null>(null)
  const [metrics, setMetrics] = useState({ original: 0, edited: 0, deleted: 0 })
  const [downloadSuccess, setDownloadSuccess] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadPdf = useCallback(async (file: File) => {
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file.')
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      setError('File exceeds 20 MB limit.')
      return
    }

    setError(null)
    setState('uploading')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/api/pdf-upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail || `Upload failed (${res.status})`)
      }
      const data = await res.json()
      setCards(data.cards)
      setMetrics({ original: data.cards.length, edited: 0, deleted: 0 })
      setState('preview')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setState('idle')
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadPdf(file)
  }, [uploadPdf])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadPdf(file)
  }, [uploadPdf])

  const deleteCard = useCallback((idx: number) => {
    setCards(prev => prev.filter((_, i) => i !== idx))
    setMetrics(prev => ({ ...prev, deleted: prev.deleted + 1 }))
    if (editingIdx === idx) setEditingIdx(null)
  }, [editingIdx])

  const updateCard = useCallback((idx: number, field: 'front' | 'back', value: string) => {
    setCards(prev => prev.map((c, i) => i === idx ? { ...c, [field]: value } : c))
  }, [])

  const downloadDeck = useCallback(async () => {
    setState('generating')
    setError(null)

    try {
      const res = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cards,
          deck_name: deckName,
          cards_original: metrics.original,
          cards_edited: metrics.edited,
          cards_deleted: metrics.deleted,
        }),
      })
      if (!res.ok) throw new Error(`Generation failed (${res.status})`)

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${deckName}.apkg`
      a.click()
      URL.revokeObjectURL(url)
      setState('preview')
      setDownloadSuccess(true)
      setTimeout(() => setDownloadSuccess(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed')
      setState('preview')
    }
  }, [cards, deckName, metrics])

  const reset = useCallback(() => {
    setCards([])
    setState('idle')
    setError(null)
    setEditingIdx(null)
    setDownloadSuccess(false)
    setMetrics({ original: 0, edited: 0, deleted: 0 })
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  return (
    <>
      <div className="header">
        <div className="logo-mark">
          <div className="logo-icon">
            <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="2" width="14" height="14" rx="2"/>
              <line x1="5.5" y1="6" x2="12.5" y2="6"/>
              <line x1="5.5" y1="9" x2="10" y2="9"/>
              <line x1="5.5" y1="12" x2="11.5" y2="12"/>
            </svg>
          </div>
        </div>
        <h1>Notes <em>to</em> Anki</h1>
        <p className="subtitle">Upload your study notes & download a ready-to-import deck</p>
      </div>

      <div className="main">
        {error && <div className="nta-error">{error}</div>}

        {/* UPLOAD / LOADING SCREEN */}
        {(state === 'idle' || state === 'uploading') && (
          <div className="screen">
            <div
              className={`upload-zone${dragOver ? ' dragging' : ''}${state === 'uploading' ? ' loading' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => state === 'idle' && fileInputRef.current?.click()}
            >
              {state === 'uploading' ? (
                <>
                  <div className="spinner" />
                  <p className="loading-text">Generating flashcards&hellip;</p>
                  <div className="progress-bar-wrap">
                    <div className="progress-bar-fill" />
                  </div>
                </>
              ) : (
                <>
                  <div className="upload-icon">
                    <svg viewBox="0 0 28 28" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M6 20h16M14 6v10M10 10l4-4 4 4"/>
                    </svg>
                  </div>
                  <p className="upload-primary">Drop your PDF here</p>
                  <p className="upload-secondary">or click anywhere to browse</p>
                  <span className="upload-hint">Supports multi-page study notes & textbooks</span>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                hidden
              />
            </div>
          </div>
        )}

        {/* GENERATING STATE */}
        {state === 'generating' && (
          <div className="screen">
            <div className="upload-zone loading">
              <div className="spinner" />
              <p className="loading-text">Building Anki deck&hellip;</p>
              <div className="progress-bar-wrap">
                <div className="progress-bar-fill" />
              </div>
            </div>
          </div>
        )}

        {/* RESULTS SCREEN */}
        {state === 'preview' && (
          <div className="screen">
            <div className="results-header">
              <div className="card-count">
                <span className="count-num">{cards.length}</span>
                <span className="count-label">card{cards.length !== 1 ? 's' : ''} generated</span>
              </div>
              <button className="btn-ghost" onClick={reset}>
                &uarr; Upload different PDF
              </button>
            </div>

            <div className="deck-row">
              <div className="input-wrap">
                <span className="input-label">Deck name</span>
                <input
                  type="text"
                  value={deckName}
                  onChange={e => setDeckName(e.target.value)}
                  placeholder="e.g. Psychiatry — Bipolar Disorder"
                />
              </div>
              {cards.length > 0 && (
                <button
                  className={`btn-download${downloadSuccess ? ' success' : ''}`}
                  onClick={downloadDeck}
                >
                  {downloadSuccess ? (
                    <>
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 8l4 4 6-6"/>
                      </svg>
                      Downloaded!
                    </>
                  ) : (
                    <>
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M8 2v8M5 7l3 3 3-3M3 13h10"/>
                      </svg>
                      Download .apkg
                    </>
                  )}
                </button>
              )}
            </div>

            {cards.length === 0 && (
              <p className="nta-empty">No cards were extracted. Make sure your PDF has bold questions with answers below them.</p>
            )}

            {cards.length > 0 && (
              <>
                <div className="divider">Preview</div>
                <div className="card-list">
                  {cards.map((card, idx) => (
                    <div
                      key={idx}
                      className="flashcard"
                      style={{ animationDelay: `${idx * 40}ms` }}
                    >
                      <div className="card-meta">
                        <div className="card-left">
                          <span className="card-num">#{idx + 1}</span>
                          {card.tags.map(tag => (
                            <span key={tag} className="card-tag">{tag}</span>
                          ))}
                        </div>
                        <div className="card-actions">
                          <button
                            className="icon-btn"
                            title={editingIdx === idx ? 'Done editing' : 'Edit'}
                            onClick={() => {
                              if (editingIdx === idx) {
                                setMetrics(prev => ({ ...prev, edited: prev.edited + 1 }))
                                setEditingIdx(null)
                              } else {
                                setEditingIdx(idx)
                              }
                            }}
                          >
                            {editingIdx === idx ? (
                              <svg viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M3 8l3 3 6-6"/>
                              </svg>
                            ) : (
                              <svg viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M10 2l3 3-8 8H2v-3L10 2z"/>
                              </svg>
                            )}
                          </button>
                          <button
                            className="icon-btn delete"
                            title="Delete"
                            onClick={() => deleteCard(idx)}
                          >
                            <svg viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                              <path d="M3 4h9M5 4V3h5v1M6 7v4M9 7v4M4 4l.5 8h6l.5-8"/>
                            </svg>
                          </button>
                        </div>
                      </div>

                      {editingIdx === idx ? (
                        <div className="card-edit">
                          <label>Front</label>
                          <textarea
                            value={card.front}
                            onChange={e => updateCard(idx, 'front', e.target.value)}
                            rows={2}
                          />
                          <label>Back</label>
                          <textarea
                            value={card.back}
                            onChange={e => updateCard(idx, 'back', e.target.value)}
                            rows={4}
                          />
                        </div>
                      ) : (
                        <>
                          <div className="card-q">
                            <span className="label-q">Q</span>
                            <span>{card.front}</span>
                          </div>
                          <div className="separator" />
                          <div className="card-a">
                            <span className="label-a">A</span>
                            <span>{card.back}</span>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div className="footer">
        <div className="footer-rule" />
        <div className="footer-text">
          <span className="footer-copy">&copy; 2026</span>
          <span className="footer-name">Danial Beg</span>
        </div>
        <div className="footer-rule" />
      </div>
    </>
  )
}
