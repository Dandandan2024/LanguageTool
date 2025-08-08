import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import pkg from 'pg';
import { updateReviewState } from './scheduler.js';

dotenv.config();
const { Pool } = pkg;

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// In-memory stores
let encounters = [];
let reviewStates = {};
let phrases = [
  { phrase_id: 101, text: "Bonjour", cefr_level: "A1" },
  { phrase_id: 102, text: "Comment ça va?", cefr_level: "A1" },
  { phrase_id: 103, text: "Je voudrais un café", cefr_level: "A1" }
];

app.get('/', (req, res) => res.json({ message: 'Backend API running' }));

// POST /encounter
app.post('/encounter', (req, res) => {
  const { user_id, phrase_id, context_id, signals, latency_ms, hints_used, raw_text } = req.body;
  if (!user_id || !phrase_id) {
    return res.status(400).json({ error: "user_id and phrase_id are required" });
  }
  const encounter = {
    encounter_id: encounters.length + 1,
    user_id,
    phrase_id,
    context_id: context_id || null,
    signals: signals || [],
    latency_ms: latency_ms || null,
    hints_used: hints_used || 0,
    raw_text: raw_text || "",
    created_at: new Date().toISOString()
  };
  encounters.push(encounter);

  const key = `${user_id}:${phrase_id}`;
  if (!reviewStates[key]) {
    reviewStates[key] = {
      user_id,
      phrase_id,
      ef: 2.5,
      interval_days: 0,
      repetitions: 0,
      due_at: new Date().toISOString(),
      last_grade: null
    };
  }
  res.json({ status: "logged", encounter });
});

// POST /grade
app.post('/grade', (req, res) => {
  const { user_id, phrase_id, grade } = req.body;
  if (!user_id || !phrase_id || grade === undefined) {
    return res.status(400).json({ error: "user_id, phrase_id, and grade are required" });
  }
  const key = `${user_id}:${phrase_id}`;
  if (!reviewStates[key]) {
    reviewStates[key] = {
      user_id,
      phrase_id,
      ef: 2.5,
      interval_days: 0,
      repetitions: 0,
      due_at: new Date().toISOString(),
      last_grade: null
    };
  }
  reviewStates[key] = updateReviewState(reviewStates[key], grade);
  res.json({ status: "graded", state: reviewStates[key] });
});

// GET /due
app.get('/due', (req, res) => {
  const { user_id, limit } = req.query;
  if (!user_id) return res.status(400).json({ error: "user_id is required" });
  const now = new Date();
  const dueItems = Object.values(reviewStates)
    .filter(s => s.user_id == user_id && new Date(s.due_at) <= now)
    .map(s => ({ ...s, phrase: phrases.find(p => p.phrase_id === s.phrase_id) }))
    .sort((a, b) => new Date(a.due_at) - new Date(b.due_at));
  res.json(limit ? dueItems.slice(0, parseInt(limit)) : dueItems);
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend listening on port ${PORT}`));
