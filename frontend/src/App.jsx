import React, { useState } from 'react';

export default function App() {
  const API_URL = 'http://localhost:5000';
  const [phraseId, setPhraseId] = useState(101);
  const [grade, setGrade] = useState(4);
  const [dueItems, setDueItems] = useState([]);
  const [logResult, setLogResult] = useState(null);
  const [gradeResult, setGradeResult] = useState(null);

  const logEncounter = async () => {
    const res = await fetch(`${API_URL}/encounter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 1, phrase_id: phraseId, signals: ['tap'], raw_text: 'test phrase' })
    });
    const data = await res.json();
    setLogResult(data);
  };

  const sendGrade = async () => {
    const res = await fetch(`${API_URL}/grade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 1, phrase_id: phraseId, grade })
    });
    const data = await res.json();
    setGradeResult(data);
  };

  const getDue = async () => {
    const res = await fetch(`${API_URL}/due?user_id=1&limit=10`);
    const data = await res.json();
    setDueItems(data);
  };

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <h1>LangTool MVP UI</h1>
      <div>
        <label>Phrase ID: </label>
        <input type="number" value={phraseId} onChange={e => setPhraseId(Number(e.target.value))} />
      </div>
      <div>
        <button onClick={logEncounter}>Log Encounter</button>
        {logResult && <pre>{JSON.stringify(logResult, null, 2)}</pre>}
      </div>
      <div>
        <label>Grade: </label>
        <input type="number" value={grade} onChange={e => setGrade(Number(e.target.value))} min="0" max="5" />
        <button onClick={sendGrade}>Send Grade</button>
        {gradeResult && <pre>{JSON.stringify(gradeResult, null, 2)}</pre>}
      </div>
      <div>
        <button onClick={getDue}>Get Due Items</button>
        <pre>{JSON.stringify(dueItems, null, 2)}</pre>
      </div>
    </div>
  );
}
