"""
Integration of contextual learning with FSRS system
"""

from contextual_learning import distribute_contextual_credit, WordCredit
from fsrs import schedule_card, Card, Rating, State
from datetime import datetime
from typing import List, Dict

def process_contextual_review(
    sentence: str,
    target_lexeme_id: str, 
    target_word: str,
    user_rating: int,
    user_id: str,
    user_cefr: str,
    db_connection
) -> Dict:
    """
    Process a review with contextual credit distribution
    """
    
    # Get contextual credit distribution
    credits = distribute_contextual_credit(
        sentence=sentence,
        target_word=target_word,
        user_rating=user_rating,
        user_cefr=user_cefr
    )
    
    results = {
        "primary_updates": 0,
        "supporting_updates": 0,
        "total_words_credited": len(credits),
        "credit_details": []
    }
    
    with db_connection.cursor() as cur:
        for credit in credits:
            # Look up lexeme_id for this word (simplified - would need proper lookup)
            if credit.credit_type.value == "primary":
                lexeme_id = target_lexeme_id
            else:
                # Look up supporting word lexeme (would implement proper lookup)
                cur.execute("""
                    SELECT l.id FROM lexemes l
                    JOIN word_forms wf ON l.id = wf.lexeme_id  
                    WHERE wf.form = %s
                    LIMIT 1
                """, (credit.word,))
                
                lexeme_result = cur.fetchone()
                if not lexeme_result:
                    continue  # Skip unknown words
                lexeme_id = lexeme_result[0]
            
            # Get current FSRS state for this lexeme
            cur.execute("""
                SELECT * FROM user_lexemes 
                WHERE user_id = %s AND lexeme_id = %s
            """, (user_id, lexeme_id))
            
            user_lexeme = cur.fetchone()
            
            if user_lexeme:
                # Load existing FSRS state
                card = Card(
                    due=user_lexeme['due_date'] or datetime.now().date(),
                    stability=user_lexeme['stability'] or 0.0,
                    difficulty=user_lexeme['difficulty'] or 0.0,
                    elapsed_days=user_lexeme['elapsed_days'] or 0,
                    scheduled_days=user_lexeme['scheduled_days'] or 0,
                    reps=user_lexeme['reps'] or 0,
                    lapses=user_lexeme['lapses'] or 0,
                    state=State[user_lexeme['state'].upper()] if user_lexeme['state'] else State.NEW,
                    last_review=user_lexeme['last_review']
                )
            else:
                # Create new card for this lexeme
                from fsrs import create_fsrs
                fsrs = create_fsrs()
                card = fsrs.init_card(datetime.now())
            
            # Apply FSRS update with adjusted rating
            updated_card, review_log = schedule_card(
                card, 
                Rating(credit.adjusted_rating), 
                datetime.now()
            )
            
            # Update database
            cur.execute("""
                INSERT INTO user_lexemes (
                    user_id, lexeme_id, stability, difficulty, interval_days,
                    due_date, reps, lapses, last_review, state,
                    scheduled_days, elapsed_days, times_seen
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, lexeme_id) 
                DO UPDATE SET
                    stability = EXCLUDED.stability,
                    difficulty = EXCLUDED.difficulty,
                    interval_days = EXCLUDED.interval_days,
                    due_date = EXCLUDED.due_date,
                    reps = EXCLUDED.reps,
                    lapses = EXCLUDED.lapses,
                    last_review = EXCLUDED.last_review,
                    state = EXCLUDED.state,
                    scheduled_days = EXCLUDED.scheduled_days,
                    elapsed_days = EXCLUDED.elapsed_days,
                    times_seen = COALESCE(user_lexemes.times_seen, 0) + 1
            """, (
                user_id, lexeme_id, updated_card.stability, updated_card.difficulty,
                updated_card.scheduled_days, updated_card.due.date(), updated_card.reps,
                updated_card.lapses, updated_card.last_review, updated_card.state.name.lower(),
                updated_card.scheduled_days, updated_card.elapsed_days, 1
            ))
            
            # Log the contextual review
            cur.execute("""
                INSERT INTO hybrid_review_log (
                    user_id, lexeme_id, content_type, question_text, 
                    user_response, rating, lexeme_stability_after, 
                    lexeme_difficulty_after
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, lexeme_id, "contextual_sentence", sentence,
                str(user_rating), credit.adjusted_rating, 
                updated_card.stability, updated_card.difficulty
            ))
            
            # Track results
            if credit.credit_type.value == "primary":
                results["primary_updates"] += 1
            else:
                results["supporting_updates"] += 1
                
            results["credit_details"].append({
                "word": credit.word,
                "type": credit.credit_type.value,
                "original_rating": user_rating,
                "adjusted_rating": credit.adjusted_rating,
                "credit_multiplier": credit.credit_multiplier,
                "new_stability": updated_card.stability,
                "next_due": updated_card.due.isoformat()
            })
    
    return results

# Example usage in main API
def handle_sentence_review(request_data, db_connection):
    """
    Handle a sentence review with contextual learning
    """
    sentence = request_data['sentence']
    target_word = request_data['target_word']
    target_lexeme_id = request_data['target_lexeme_id']
    user_rating = request_data['rating']
    user_id = request_data['username']
    user_cefr = request_data.get('user_cefr', 'B1')
    
    # Process with contextual credit
    results = process_contextual_review(
        sentence=sentence,
        target_lexeme_id=target_lexeme_id,
        target_word=target_word,
        user_rating=user_rating,
        user_id=user_id,
        user_cefr=user_cefr,
        db_connection=db_connection
    )
    
    return {
        "success": True,
        "message": f"Updated {results['total_words_credited']} words",
        "primary_word_updates": results["primary_updates"],
        "supporting_word_updates": results["supporting_updates"],
        "details": results["credit_details"]
    }
