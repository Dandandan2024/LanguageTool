"""
FSRS v4 (Free Spaced Repetition Scheduler) Implementation
Based on the official FSRS algorithm with default parameters.

References:
- https://github.com/open-spaced-repetition/fsrs4anki
- https://github.com/open-spaced-repetition/py-fsrs
"""

import math
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Tuple, Optional
from enum import IntEnum

class Rating(IntEnum):
    """FSRS rating scale"""
    AGAIN = 1   # Incorrect/forgot
    HARD = 2    # Correct but difficult
    GOOD = 3    # Correct with some effort
    EASY = 4    # Correct and easy

class State(IntEnum):
    """Card learning state"""
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3

@dataclass
class Card:
    """FSRS Card state"""
    due: datetime
    stability: float
    difficulty: float
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: State
    last_review: Optional[datetime] = None

@dataclass
class ReviewLog:
    """Review log entry"""
    rating: Rating
    elapsed_days: int
    scheduled_days: int
    review: datetime
    state: State

class FSRS:
    """
    FSRS v4 Algorithm Implementation
    
    Default parameters based on the reference implementation
    """
    
    def __init__(self):
        # FSRS v4 default parameters (optimized from large datasets)
        self.w = [
            0.4072,   # w[0]: initial stability for Again
            1.1829,   # w[1]: initial stability for Hard  
            3.1262,   # w[2]: initial stability for Good
            15.4722,  # w[3]: initial stability for Easy
            7.2102,   # w[4]: initial difficulty decay
            0.5316,   # w[5]: initial difficulty for Hard
            1.0651,   # w[6]: initial difficulty for Good
            0.0234,   # w[7]: initial difficulty for Easy
            1.616,    # w[8]: stability increase for Again
            0.1544,   # w[9]: stability increase for Hard
            1.0824,   # w[10]: stability increase for Good
            1.9813,   # w[11]: stability increase for Easy
            0.0953,   # w[12]: difficulty decay
            0.2975,   # w[13]: difficulty increase for Again
            2.2042,   # w[14]: difficulty increase for Hard
            0.2407,   # w[15]: difficulty decrease for Good
            2.9466,   # w[16]: difficulty decrease for Easy
            0.5034,   # w[17]: stability factor for short intervals
            1.6567    # w[18]: stability factor for long intervals
        ]
        
        # Learning steps (in minutes)
        self.learning_steps = [1, 10]  # 1 minute, 10 minutes
        self.relearning_steps = [10]   # 10 minutes
        
        # Graduating intervals
        self.graduating_interval_good = 1  # 1 day
        self.graduating_interval_easy = 4  # 4 days
        
        # Other parameters
        self.maximum_interval = 36500  # 100 years in days
        self.hard_interval_factor = 1.2
        
    def init_card(self, now: datetime) -> Card:
        """Initialize a new card"""
        return Card(
            due=now,
            stability=0.0,
            difficulty=0.0,
            elapsed_days=0,
            scheduled_days=0,
            reps=0,
            lapses=0,
            state=State.NEW,
            last_review=None
        )
    
    def repeat(self, card: Card, now: datetime) -> dict:
        """
        Generate scheduling cards for all possible ratings
        Returns dict with Rating as key and (Card, ReviewLog) as value
        """
        if card.state == State.NEW:
            return self._repeat_new_card(card, now)
        elif card.state in [State.LEARNING, State.RELEARNING]:
            return self._repeat_learning_card(card, now)
        else:  # State.REVIEW
            return self._repeat_review_card(card, now)
    
    def _repeat_new_card(self, card: Card, now: datetime) -> dict:
        """Handle new card scheduling"""
        scheduled_cards = {}
        
        # Calculate initial difficulty
        init_difficulty = self._init_difficulty(Rating.GOOD)
        
        for rating in Rating:
            new_card = Card(
                due=now,
                stability=self._init_stability(rating),
                difficulty=init_difficulty,
                elapsed_days=0,
                scheduled_days=0,
                reps=1,
                lapses=1 if rating == Rating.AGAIN else 0,
                state=State.LEARNING if rating == Rating.AGAIN else State.REVIEW,
                last_review=now
            )
            
            # Schedule next review
            if rating == Rating.AGAIN:
                new_card.due = now + timedelta(minutes=self.learning_steps[0])
                new_card.scheduled_days = 0
            elif rating == Rating.HARD:
                new_card.due = now + timedelta(minutes=self.learning_steps[-1])
                new_card.scheduled_days = 0
            elif rating == Rating.GOOD:
                new_card.due = now + timedelta(days=self.graduating_interval_good)
                new_card.scheduled_days = self.graduating_interval_good
            else:  # EASY
                new_card.due = now + timedelta(days=self.graduating_interval_easy)
                new_card.scheduled_days = self.graduating_interval_easy
                new_card.difficulty = self._init_difficulty(Rating.EASY)
            
            review_log = ReviewLog(
                rating=rating,
                elapsed_days=0,
                scheduled_days=new_card.scheduled_days,
                review=now,
                state=card.state
            )
            
            scheduled_cards[rating] = (new_card, review_log)
        
        return scheduled_cards
    
    def _repeat_learning_card(self, card: Card, now: datetime) -> dict:
        """Handle learning/relearning card scheduling"""
        scheduled_cards = {}
        elapsed_days = max(0, (now - card.last_review).days) if card.last_review else 0
        
        for rating in Rating:
            new_card = Card(
                due=card.due,
                stability=card.stability,
                difficulty=card.difficulty,
                elapsed_days=elapsed_days,
                scheduled_days=card.scheduled_days,
                reps=card.reps + 1,
                lapses=card.lapses,
                state=card.state,
                last_review=now
            )
            
            if rating == Rating.AGAIN:
                # Stay in learning, reset to first step
                new_card.due = now + timedelta(minutes=self.learning_steps[0])
                new_card.scheduled_days = 0
                new_card.lapses += 1
            elif rating in [Rating.HARD, Rating.GOOD]:
                if card.state == State.LEARNING:
                    # Graduate to review
                    new_card.state = State.REVIEW
                    interval = self.graduating_interval_good if rating == Rating.GOOD else 1
                    new_card.due = now + timedelta(days=interval)
                    new_card.scheduled_days = interval
                else:  # RELEARNING
                    # Graduate back to review
                    new_card.state = State.REVIEW
                    new_card.stability = self._next_stability(card, elapsed_days, rating)
                    new_card.difficulty = self._next_difficulty(card, rating)
                    interval = max(1, int(new_card.stability * self.hard_interval_factor)) if rating == Rating.HARD else max(1, int(new_card.stability))
                    new_card.due = now + timedelta(days=interval)
                    new_card.scheduled_days = interval
            else:  # EASY
                # Graduate to review with easy interval
                new_card.state = State.REVIEW
                if card.state == State.LEARNING:
                    new_card.difficulty = self._init_difficulty(Rating.EASY)
                    interval = self.graduating_interval_easy
                else:  # RELEARNING
                    new_card.stability = self._next_stability(card, elapsed_days, rating)
                    new_card.difficulty = self._next_difficulty(card, rating)
                    interval = max(self.graduating_interval_easy, int(new_card.stability))
                new_card.due = now + timedelta(days=interval)
                new_card.scheduled_days = interval
            
            review_log = ReviewLog(
                rating=rating,
                elapsed_days=elapsed_days,
                scheduled_days=new_card.scheduled_days,
                review=now,
                state=card.state
            )
            
            scheduled_cards[rating] = (new_card, review_log)
        
        return scheduled_cards
    
    def _repeat_review_card(self, card: Card, now: datetime) -> dict:
        """Handle review card scheduling"""
        scheduled_cards = {}
        elapsed_days = max(0, (now - card.last_review).days) if card.last_review else 0
        
        for rating in Rating:
            new_card = Card(
                due=card.due,
                stability=card.stability,
                difficulty=card.difficulty,
                elapsed_days=elapsed_days,
                scheduled_days=card.scheduled_days,
                reps=card.reps + 1,
                lapses=card.lapses,
                state=card.state,
                last_review=now
            )
            
            if rating == Rating.AGAIN:
                # Move to relearning
                new_card.state = State.RELEARNING
                new_card.due = now + timedelta(minutes=self.relearning_steps[0])
                new_card.scheduled_days = 0
                new_card.lapses += 1
                new_card.stability = self._next_stability(card, elapsed_days, rating)
                new_card.difficulty = self._next_difficulty(card, rating)
            else:
                # Stay in review
                new_card.stability = self._next_stability(card, elapsed_days, rating)
                new_card.difficulty = self._next_difficulty(card, rating)
                
                if rating == Rating.HARD:
                    interval = max(1, int(new_card.stability * self.hard_interval_factor))
                else:  # GOOD or EASY
                    interval = max(1, int(new_card.stability))
                
                interval = min(interval, self.maximum_interval)
                new_card.due = now + timedelta(days=interval)
                new_card.scheduled_days = interval
            
            review_log = ReviewLog(
                rating=rating,
                elapsed_days=elapsed_days,
                scheduled_days=new_card.scheduled_days,
                review=now,
                state=card.state
            )
            
            scheduled_cards[rating] = (new_card, review_log)
        
        return scheduled_cards
    
    def _init_stability(self, rating: Rating) -> float:
        """Calculate initial stability for new cards"""
        return max(0.1, self.w[rating - 1])  # w[0] to w[3]
    
    def _init_difficulty(self, rating: Rating) -> float:
        """Calculate initial difficulty for new cards"""
        if rating == Rating.EASY:
            return max(1.0, self.w[4] - self.w[7])
        else:
            return max(1.0, self.w[4] - self.w[rating + 3])  # w[5], w[6], w[7]
    
    def _next_stability(self, card: Card, elapsed_days: int, rating: Rating) -> float:
        """Calculate next stability using FSRS formula"""
        if rating == Rating.AGAIN:
            stability = self.w[8] * math.pow(card.difficulty, -self.w[9]) * \
                       (math.pow(card.stability + 1, self.w[10]) - 1) * \
                       math.exp((1 - self._retrievability(card, elapsed_days)) * self.w[11])
        else:
            stability = card.stability * (
                math.exp(self.w[12]) * 
                (11 - card.difficulty) * 
                math.pow(card.stability, -self.w[13]) * 
                (math.exp((rating - 3) * self.w[14]) - 1) * 
                self._retrievability(card, elapsed_days) + 1
            )
        
        return max(0.1, min(stability, self.maximum_interval))
    
    def _next_difficulty(self, card: Card, rating: Rating) -> float:
        """Calculate next difficulty using FSRS formula"""
        next_difficulty = card.difficulty - self.w[15] * (rating - 3)
        
        # Mean reversion
        mean_reversion = self.w[16] * (self._init_difficulty(Rating.GOOD) - card.difficulty)
        next_difficulty += mean_reversion
        
        return max(1.0, min(10.0, next_difficulty))
    
    def _retrievability(self, card: Card, elapsed_days: int) -> float:
        """Calculate retrievability (probability of recall)"""
        if card.stability <= 0:
            return 0.0
        return math.pow(1 + elapsed_days / (9 * card.stability), -1)
    
    def get_retrievability(self, card: Card, now: datetime) -> float:
        """Get current retrievability of a card"""
        if card.last_review is None:
            return 0.0
        elapsed_days = max(0, (now - card.last_review).days)
        return self._retrievability(card, elapsed_days)

# Convenience functions for the main API
def create_fsrs() -> FSRS:
    """Create FSRS instance with default parameters"""
    return FSRS()

def schedule_card(card: Card, rating: Rating, now: datetime) -> Tuple[Card, ReviewLog]:
    """
    Schedule a card based on rating
    Returns the updated card and review log
    """
    fsrs = create_fsrs()
    scheduled_cards = fsrs.repeat(card, now)
    return scheduled_cards[rating]
