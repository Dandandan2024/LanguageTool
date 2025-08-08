'use client'
import { useState, useEffect } from 'react'

export default function Home() {
  const [cards, setCards] = useState([])
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Use environment variable for API URL, fallback to local development
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002'

  // Fetch cards from API
  useEffect(() => {
    fetchCards()
  }, [])

  const fetchCards = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/v1/sessions/next`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ count: 10 })
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch cards')
      }
      
      const data = await response.json()
      setCards(data.items)
      setCurrentCardIndex(0)
      setShowAnswer(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const submitReview = async (rating) => {
    const currentCard = cards[currentCardIndex]
    
    try {
      await fetch(`${API_BASE}/v1/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify([{
          card_id: currentCard.card_id,
          rating: rating,
          response_time_ms: 3000 // placeholder
        }])
      })

      // Move to next card
      if (currentCardIndex < cards.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1)
        setShowAnswer(false)
      } else {
        // All cards reviewed, fetch more
        fetchCards()
      }
    } catch (err) {
      setError('Failed to submit review')
    }
  }

  const renderCard = (card) => {
    if (!card) return null

    const { type, payload } = card

    switch (type) {
      case 'cloze':
        return (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <h2>Fill in the blank:</h2>
            <p style={{ fontSize: '1.5rem', margin: '1rem 0' }}>
              {payload.text}
            </p>
            {showAnswer && (
              <div style={{ backgroundColor: '#f0f8ff', padding: '1rem', borderRadius: '8px' }}>
                <p><strong>Answer:</strong> {payload.answer}</p>
                {payload.hints && (
                  <p><strong>Hint:</strong> {payload.hints.join(', ')}</p>
                )}
              </div>
            )}
          </div>
        )
      
      case 'vocabulary':
        return (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <h2>Vocabulary:</h2>
            <p style={{ fontSize: '2rem', margin: '1rem 0' }}>
              {payload.word}
            </p>
            {showAnswer && (
              <div style={{ backgroundColor: '#f0f8ff', padding: '1rem', borderRadius: '8px' }}>
                <p><strong>Translation:</strong> {payload.translation}</p>
                <p><strong>Level:</strong> {payload.difficulty}</p>
              </div>
            )}
          </div>
        )
      
      case 'sentence':
        return (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <h2>Translate:</h2>
            <p style={{ fontSize: '1.5rem', margin: '1rem 0' }}>
              {payload.spanish}
            </p>
            {showAnswer && (
              <div style={{ backgroundColor: '#f0f8ff', padding: '1rem', borderRadius: '8px' }}>
                <p><strong>English:</strong> {payload.english}</p>
                <p><strong>Level:</strong> {payload.difficulty}</p>
              </div>
            )}
          </div>
        )
      
      default:
        return <p>Unknown card type: {type}</p>
    }
  }

  if (loading) {
    return (
      <main style={{padding: 24, maxWidth: 720, margin: '0 auto', textAlign: 'center'}}>
        <h1>Adaptive SRS — Review</h1>
        <p>Loading cards...</p>
      </main>
    )
  }

  if (error) {
    return (
      <main style={{padding: 24, maxWidth: 720, margin: '0 auto', textAlign: 'center'}}>
        <h1>Adaptive SRS — Review</h1>
        <p style={{color: 'red'}}>Error: {error}</p>
        <button onClick={fetchCards} style={{padding: '0.5rem 1rem', marginTop: '1rem'}}>
          Try Again
        </button>
      </main>
    )
  }

  if (!cards.length) {
    return (
      <main style={{padding: 24, maxWidth: 720, margin: '0 auto', textAlign: 'center'}}>
        <h1>Adaptive SRS — Review</h1>
        <p>No cards available.</p>
        <button onClick={fetchCards} style={{padding: '0.5rem 1rem', marginTop: '1rem'}}>
          Refresh
        </button>
      </main>
    )
  }

  const currentCard = cards[currentCardIndex]

  return (
    <main style={{padding: 24, maxWidth: 720, margin: '0 auto'}}>
      <h1>Adaptive SRS — Review</h1>
      <p>Card {currentCardIndex + 1} of {cards.length}</p>
      
      {renderCard(currentCard)}
      
      {!showAnswer ? (
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <button 
            onClick={() => setShowAnswer(true)}
            style={{
              padding: '1rem 2rem',
              fontSize: '1.2rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Show Answer
          </button>
        </div>
      ) : (
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <p style={{ marginBottom: '1rem' }}>How well did you know this?</p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              onClick={() => submitReview(1)}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Again (1)
            </button>
            <button 
              onClick={() => submitReview(2)}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#ffc107',
                color: 'black',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Hard (2)
            </button>
            <button 
              onClick={() => submitReview(3)}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Good (3)
            </button>
            <button 
              onClick={() => submitReview(4)}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#17a2b8',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Easy (4)
            </button>
          </div>
        </div>
      )}
    </main>
  )
}
