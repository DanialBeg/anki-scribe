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
  }, [])

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
        body: JSON.stringify({ cards, deck_name: deckName }),
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed')
      setState('preview')
    }
  }, [cards, deckName])

  const reset = useCallback(() => {
    setCards([])
    setState('idle')
    setError(null)
    setEditingIdx(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  return (
    <div className="nta-container">
      <header className="nta-header">
        <h1>Notes to Anki</h1>
        <p className="nta-subtitle">Upload a PDF of your study notes and download an Anki deck</p>
      </header>

      {error && <div className="nta-error">{error}</div>}

      {state === 'idle' && (
        <div
          className={`nta-upload-zone ${dragOver ? 'nta-upload-zone--active' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="nta-upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="12" y2="12" />
              <line x1="15" y1="15" x2="12" y2="12" />
            </svg>
          </div>
          <p className="nta-upload-text">Drag & drop your PDF here</p>
          <p className="nta-upload-hint">or click to browse</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            hidden
          />
        </div>
      )}

      {state === 'uploading' && (
        <div className="nta-spinner-container">
          <div className="nta-spinner" />
          <p>Extracting cards from PDF...</p>
        </div>
      )}

      {state === 'generating' && (
        <div className="nta-spinner-container">
          <div className="nta-spinner" />
          <p>Building Anki deck...</p>
        </div>
      )}

      {state === 'preview' && (
        <div className="nta-preview">
          <div className="nta-preview-header">
            <span className="nta-card-count">{cards.length} card{cards.length !== 1 ? 's' : ''} found</span>
            <button className="nta-btn nta-btn--secondary" onClick={reset}>Upload different PDF</button>
          </div>

          <div className="nta-deck-name">
            <label htmlFor="deck-name">Deck name</label>
            <input
              id="deck-name"
              type="text"
              value={deckName}
              onChange={e => setDeckName(e.target.value)}
            />
          </div>

          {cards.length === 0 && (
            <p className="nta-empty">No cards were extracted. Make sure your PDF has bold questions with answers below them.</p>
          )}

          <div className="nta-card-list">
            {cards.map((card, idx) => (
              <div key={idx} className="nta-card">
                <div className="nta-card-header">
                  <span className="nta-card-number">#{idx + 1}</span>
                  {card.tags.length > 0 && (
                    <div className="nta-tags">
                      {card.tags.map(tag => (
                        <span key={tag} className="nta-tag">{tag}</span>
                      ))}
                    </div>
                  )}
                  <div className="nta-card-actions">
                    <button
                      className="nta-btn-icon"
                      onClick={() => setEditingIdx(editingIdx === idx ? null : idx)}
                      title={editingIdx === idx ? 'Done editing' : 'Edit card'}
                    >
                      {editingIdx === idx ? '✓' : '✎'}
                    </button>
                    <button
                      className="nta-btn-icon nta-btn-icon--delete"
                      onClick={() => deleteCard(idx)}
                      title="Delete card"
                    >
                      ×
                    </button>
                  </div>
                </div>

                {editingIdx === idx ? (
                  <div className="nta-card-edit">
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
                  <div className="nta-card-body">
                    <div className="nta-card-front">
                      <strong>Q:</strong> {card.front}
                    </div>
                    <div className="nta-card-back">
                      <strong>A:</strong> {card.back}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {cards.length > 0 && (
            <button className="nta-btn nta-btn--primary" onClick={downloadDeck}>
              Download .apkg
            </button>
          )}
        </div>
      )}
    </div>
  )
}
