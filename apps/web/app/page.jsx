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
  const [currentView, setCurrentView] = useState('study') // 'study', 'stats', or 'placement'
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(false)
  
  // Placement test state
  const [placementSession, setPlacementSession] = useState(null)
  const [placementItem, setPlacementItem] = useState(null)
  const [placementLoading, setPlacementLoading] = useState(false)
  const [placementResults, setPlacementResults] = useState(null)
  const [selectedAnswer, setSelectedAnswer] = useState('')

  // Use environment variable for API URL, fallback to local development
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002'

  // Fetch cards from API when username is set
  useEffect(() => {
    if (username && isUsernameSet) {
      fetchCards()
    }
  }, [username, isUsernameSet])

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
    setCurrentView('study')
    setStats(null)
  }

  const fetchStats = async () => {
    if (!username) return
    
    try {
      setStatsLoading(true)
      const response = await fetch(`${API_BASE}/v1/stats/${username}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch stats')
      }
      
      const data = await response.json()
      setStats(data)
    } catch (err) {
      console.error('Stats error:', err)
      setError('Failed to load statistics')
    } finally {
      setStatsLoading(false)
    }
  }

  // Placement test functions
  const startPlacementTest = async (claimedLevel = null) => {
    if (!username) return
    try {
      setPlacementLoading(true)
      setError(null)
      
      const response = await fetch(`${API_BASE}/v1/placement/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          language: 'en',
          claimed_level: claimedLevel
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to start placement test')
      }
      
      const data = await response.json()
      setPlacementSession(data.session_id)
      setPlacementItem(data.item)
      setSelectedAnswer('')
      
    } catch (err) {
      console.error('Placement start error:', err)
      setError('Failed to start placement test')
    } finally {
      setPlacementLoading(false)
    }
  }

  const submitPlacementAnswer = async () => {
    if (!placementSession || !placementItem || !selectedAnswer) return
    
    try {
      setPlacementLoading(true)
      
      const response = await fetch(`${API_BASE}/v1/placement/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: placementSession,
          card_id: placementItem.id,
          user_answer: selectedAnswer,
          response_time_ms: 0
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to submit answer')
      }
      
      const data = await response.json()
      
      if (data.complete) {
        // Test completed
        setPlacementResults(data.results)
        setPlacementItem(null)
      } else {
        // Next question
        setPlacementItem(data.item)
        setSelectedAnswer('')
      }
      
    } catch (err) {
      console.error('Placement answer error:', err)
      setError('Failed to submit answer')
    } finally {
      setPlacementLoading(false)
    }
  }

  const fetchCards = async () => {
    if (!username) return // Don't fetch cards without a username
    
    try {
      setLoading(true)
      console.log('API_BASE:', API_BASE) // Debug: show what URL we're using
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

  const currentCard = cards[currentCardIndex]

  const renderStatsView = () => {
    if (statsLoading) {
      return <div style={{ textAlign: 'center', padding: '2rem' }}>Loading statistics...</div>
    }

    if (!stats) {
      return <div style={{ textAlign: 'center', padding: '2rem' }}>No statistics available</div>
    }

    return (
      <div>
        <h2>📊 Your Learning Statistics</h2>
        
        {/* Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#495057' }}>Total Reviews</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#007bff' }}>{stats.total_reviews}</div>
          </div>
          
          <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#495057' }}>Accuracy</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#28a745' }}>{stats.accuracy_percentage}%</div>
          </div>
          
          <div style={{ padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: '#495057' }}>Study Streak</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#fd7e14' }}>{stats.study_streak_days} days</div>
          </div>
        </div>

        {/* Language Breakdown */}
        {stats.language_breakdown.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            <h3>🌍 Languages</h3>
            {stats.language_breakdown.map(lang => (
              <div key={lang.language} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
                <span>{lang.language.toUpperCase()}</span>
                <span><strong>{lang.reviews}</strong> reviews</span>
              </div>
            ))}
          </div>
        )}

        {/* Rating Breakdown */}
        {stats.ratings_breakdown.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            <h3>⭐ Rating Distribution</h3>
            {stats.ratings_breakdown.map(rating => {
              const ratingLabels = { 1: 'Again', 2: 'Hard', 3: 'Good', 4: 'Easy' }
              const colors = { 1: '#dc3545', 2: '#fd7e14', 3: '#28a745', 4: '#007bff' }
              return (
                <div key={rating.rating} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', backgroundColor: colors[rating.rating], borderRadius: '50%' }}></div>
                    <span>{ratingLabels[rating.rating]}</span>
                  </div>
                  <span><strong>{rating.count}</strong></span>
                </div>
              )
            })}
          </div>
        )}

        {/* Recent Activity */}
        {stats.daily_activity.length > 0 && (
          <div>
            <h3>📈 Recent Activity</h3>
            {stats.daily_activity.slice(0, 10).map(day => (
              <div key={day.date} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
                <span>{new Date(day.date).toLocaleDateString()}</span>
                <span><strong>{day.count}</strong> reviews</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderPlacementView = () => {
    // Welcome screen - no session started
    if (!placementSession && !placementResults) {
      return (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h2>🎯 Adaptive Placement Test</h2>
          <p style={{ fontSize: '1.1rem', lineHeight: '1.6', marginBottom: '2rem', color: '#495057' }}>
            This intelligent test will determine your CEFR level (A1-C2) in just 7-12 questions.
            <br />
            The questions adapt to your ability - getting harder or easier based on your answers.
          </p>
          
          <div style={{ backgroundColor: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem', textAlign: 'left' }}>
            <h3 style={{ margin: '0 0 1rem 0' }}>📋 How it works:</h3>
            <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
              <li>Start at intermediate level (B1)</li>
              <li>Questions get harder if you're doing well</li>
              <li>Questions get easier if you're struggling</li>
              <li>Stops when we're confident about your level</li>
              <li>Get your CEFR level + personalized word list</li>
            </ul>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <p style={{ marginBottom: '1rem' }}>Optional: What level do you think you are?</p>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
              {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(level => (
                <button
                  key={level}
                  onClick={() => startPlacementTest(level)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#e9ecef',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                  disabled={placementLoading}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => startPlacementTest()}
            disabled={placementLoading}
            style={{
              padding: '1rem 2rem',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1.1rem',
              cursor: placementLoading ? 'not-allowed' : 'pointer',
              opacity: placementLoading ? 0.6 : 1
            }}
          >
            {placementLoading ? 'Starting Test...' : '🚀 Start Placement Test'}
          </button>
        </div>
      )
    }

    // Test completed - show results
    if (placementResults) {
      return (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h2>🎉 Placement Test Complete!</h2>
          
          <div style={{ backgroundColor: '#d4edda', padding: '2rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#155724' }}>Your CEFR Level:</h3>
            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#28a745', marginBottom: '1rem' }}>
              {placementResults.cefr_level}
            </div>
            <p style={{ margin: 0, color: '#155724' }}>
              {placementResults.items_completed} questions completed
              <br />
              Confidence: {Math.round((1 - (placementResults.confidence_interval[1] - placementResults.confidence_interval[0]) / 4) * 100)}%
            </p>
          </div>

          {placementResults.known_words && (
            <div style={{ backgroundColor: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem', textAlign: 'left' }}>
              <h3 style={{ margin: '0 0 1rem 0' }}>📚 Your Known Words (first 20):</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {placementResults.known_words.slice(0, 20).map(word => (
                  <span key={word} style={{ 
                    padding: '0.25rem 0.5rem', 
                    backgroundColor: '#007bff', 
                    color: 'white', 
                    borderRadius: '4px', 
                    fontSize: '0.9rem' 
                  }}>
                    {word}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              onClick={() => {
                setPlacementResults(null)
                setPlacementSession(null)
                setPlacementItem(null)
              }}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              Take Test Again
            </button>
            <button
              onClick={() => setCurrentView('study')}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}
            >
              Start Studying
            </button>
          </div>
        </div>
      )
    }

    // Test in progress - show current question
    if (placementItem) {
      return (
        <div style={{ padding: '2rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h2>🎯 Placement Test</h2>
            <div style={{ backgroundColor: '#e3f2fd', padding: '1rem', borderRadius: '6px', display: 'inline-block' }}>
              <strong>Current estimate: {placementItem.cefr || 'B1'}</strong>
            </div>
          </div>

          <div style={{ backgroundColor: '#f8f9fa', padding: '2rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <h3 style={{ marginBottom: '1.5rem' }}>Complete the sentence:</h3>
            <p style={{ fontSize: '1.2rem', lineHeight: '1.6', marginBottom: '2rem' }}>
              {placementItem.text}
            </p>

            <div style={{ display: 'grid', gap: '1rem' }}>
              {placementItem.options?.map((option, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedAnswer(option)}
                  style={{
                    padding: '1rem',
                    backgroundColor: selectedAnswer === option ? '#007bff' : 'white',
                    color: selectedAnswer === option ? 'white' : '#495057',
                    border: selectedAnswer === option ? '2px solid #007bff' : '2px solid #dee2e6',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontSize: '1rem'
                  }}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div style={{ textAlign: 'center' }}>
            <button
              onClick={submitPlacementAnswer}
              disabled={!selectedAnswer || placementLoading}
              style={{
                padding: '1rem 2rem',
                backgroundColor: selectedAnswer && !placementLoading ? '#28a745' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1.1rem',
                cursor: selectedAnswer && !placementLoading ? 'pointer' : 'not-allowed'
              }}
            >
              {placementLoading ? 'Processing...' : 'Submit Answer'}
            </button>
          </div>
        </div>
      )
    }

    return <div style={{ textAlign: 'center', padding: '2rem' }}>Loading...</div>
  }

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
      
      {/* Navigation */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <button
          onClick={() => setCurrentView('study')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: currentView === 'study' ? '#007bff' : '#e9ecef',
            color: currentView === 'study' ? 'white' : '#495057',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          📚 Study
        </button>
        <button
          onClick={() => setCurrentView('placement')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: currentView === 'placement' ? '#28a745' : '#e9ecef',
            color: currentView === 'placement' ? 'white' : '#495057',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          🎯 Placement Test
        </button>
        <button
          onClick={() => {
            setCurrentView('stats')
            fetchStats()
          }}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: currentView === 'stats' ? '#007bff' : '#e9ecef',
            color: currentView === 'stats' ? 'white' : '#495057',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          📊 Statistics
        </button>
      </div>

      <p>👤 Learning as: <strong>{username}</strong></p>
      
      {currentView === 'stats' ? renderStatsView() : 
       currentView === 'placement' ? renderPlacementView() : (
        <>
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
        </>
      )}
    </main>
  )
}
