import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import pkg from 'pg';

dotenv.config();
const { Pool } = pkg;

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// In-memory store for MVP
let encounters = [];

app.get('/', (req, res) => {
  res.json({ message: 'Backend API running' });
});

app.get('/health', async (req, res) => {
  try {
    const dbRes = await pool.query('SELECT NOW()');
    res.json({ status: 'ok', db_time: dbRes.rows[0] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ status: 'error', error: err.message });
  }
});

// POST /encounter - logs a user phrase encounter
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
  res.json({ status: "logged", encounter });
});

// GET /encounter - returns all logged encounters (MVP)
app.get('/encounter', (req, res) => {
  res.json({ count: encounters.length, encounters });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Backend listening on port ${PORT}`);
});
