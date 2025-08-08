export function updateReviewState(state, grade) {
  if (grade < 3) {
    state.repetitions = 0;
    state.interval_days = 1;
  } else {
    if (state.repetitions === 0) {
      state.interval_days = 1;
    } else if (state.repetitions === 1) {
      state.interval_days = 3;
    } else {
      state.interval_days = Math.round(state.interval_days * state.ef);
    }
    state.repetitions += 1;
  }

  // Ease factor update
  state.ef = Math.max(1.3, state.ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)));
  const now = new Date();
  state.due_at = new Date(now.getTime() + state.interval_days * 24 * 60 * 60 * 1000).toISOString();
  state.last_grade = grade;
  return state;
}
