'use client'
import { useState, useEffect } from 'react'
// Force deployment update

export default function Home() {
  const [cards, setCards] = useState([])
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [username, setUsername] = useState('')
  const [isUsernameSet, setIsUsernameSet] = useState(false)

  // Use environment variable for API URL, fallback to local development
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002'

  // Fetch cards from API when username is set
  useEffect(() => {
    if (username && isUsernameSet) {
      fetchCards()
    }
  }, [username, isUsernameSet])

  const fetchCards = async () => {
    if (!username) return // Don't fetch cards without a username
    
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/v1/sessions/next`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ count: 10, username: username })
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
          response_time_ms: 3000, // placeholder
          username: username
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

  // Show username input FIRST if not set
  if (!isUsernameSet) {
    return (
      <main style={{padding: 24, maxWidth: 720, margin: '0 auto', textAlign: 'center'}}>
        <h1>Adaptive SRS — Language Learning v5.0 FINAL</h1>
        <div style={{ marginTop: '2rem' }}>
          <h2>Welcome! 👋</h2>
          <p>Enter your name to start learning and track your progress:</p>
          <form onSubmit={handleUsernameSubmit} style={{ marginTop: '1.5rem' }}>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              style={{
                padding: '0.75rem',
                fontSize: '1rem',
                border: '2px solid #ddd',
                borderRadius: '0.5rem',
                marginRight: '0.5rem',
                minWidth: '200px'
              }}
              required
            />
            <button 
              type="submit"
              style={{
                padding: '0.75rem 1.5rem',
                fontSize: '1rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: 'pointer'
              }}
            >
              Start Learning
            </button>
          </form>
        </div>
      </main>
    )
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

  const handleUsernameSubmit = (e) => {
    e.preventDefault()
    if (username.trim()) {
      setIsUsernameSet(true)
      fetchCards()
    }
  }

  const handleUsernameChange = () => {
    setIsUsernameSet(false)
    setCards([])
    setCurrentCardIndex(0)
    setShowAnswer(false)
    setUsername('')
  }



  const currentCard = cards[currentCardIndex]

  return (
    <main style={{padding: 24, maxWidth: 720, margin: '0 auto'}}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1>Adaptive SRS — Review</h1>
        <button 
          onClick={handleUsernameChange}
          style={{
            padding: '0.5rem 1rem',
            fontSize: '0.9rem',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Change User
        </button>
      </div>
      <p>👤 Learning as: <strong>{username}</strong></p>
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
