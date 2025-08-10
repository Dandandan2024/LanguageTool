"""
Computerized Adaptive Testing (CAT) Algorithm for CEFR Placement
Based on Item Response Theory (IRT) with 2PL model
"""
import math
import random
from typing import Dict, List, Tuple, Optional

class PlacementCAT:
    """Computerized Adaptive Testing for CEFR placement"""
    
    def __init__(self):
        # CEFR level mappings
        self.cefr_levels = {
            "A1": -2.0, "A2": -1.0, "B1": 0.0, 
            "B2": 1.0, "C1": 2.0, "C2": 3.0
        }
        self.theta_to_cefr = {v: k for k, v in self.cefr_levels.items()}
        
        # CAT parameters
        self.initial_theta = 0.0  # Start at B1
        self.initial_se = 1.0     # Initial standard error
        self.target_se = 0.3      # Stop when SE ≤ 0.3
        self.max_items = 12       # Maximum items
        self.min_items = 7        # Minimum items
        
    def start_session(self, user_claimed_level: Optional[str] = None) -> Dict:
        """Start a new placement session"""
        if user_claimed_level and user_claimed_level in self.cefr_levels:
            initial_theta = self.cefr_levels[user_claimed_level]
        else:
            initial_theta = self.initial_theta
            
        return {
            "theta": initial_theta,
            "se": self.initial_se,
            "items_completed": 0,
            "is_complete": False
        }
    
    def select_next_item(self, current_theta: float, available_items: List[Dict]) -> Optional[Dict]:
        """Select the most informative item for current ability estimate"""
        if not available_items:
            return None
            
        best_item = None
        max_information = 0
        
        for item in available_items:
            theta_item = item.get('theta', 0.0)
            # Information function: higher when item difficulty matches ability
            information = self._item_information(current_theta, theta_item)
            
            if information > max_information:
                max_information = information
                best_item = item
                
        return best_item
    
    def update_ability(self, current_theta: float, current_se: float, 
                      item_theta: float, is_correct: bool, confidence: float = 1.0) -> Tuple[float, float]:
        """Update ability estimate using Bayesian approach"""
        
        # Item discrimination (a) and difficulty (b) parameters
        discrimination = 1.5  # Fixed discrimination for simplicity
        difficulty = item_theta
        
        # Calculate likelihood
        prob_correct = self._probability_correct(current_theta, difficulty, discrimination)
        
        # Bayesian update
        if is_correct:
            likelihood = prob_correct * confidence
        else:
            likelihood = (1 - prob_correct) * confidence
            
        # More aggressive Bayesian update for better placement accuracy
        base_learning_rate = 0.5  # Increased from 0.3 for faster convergence
        
        if is_correct:
            # Step up based on how unexpected the correct answer was
            surprise_factor = (1 - prob_correct)  # Higher if item was harder than expected
            theta_change = base_learning_rate * surprise_factor * confidence
            new_theta = current_theta + theta_change
        else:
            # Step down more aggressively - user doesn't know items at this level
            surprise_factor = prob_correct  # Higher if we expected them to get it right
            # Extra aggressive for placement (2x multiplier)
            theta_change = base_learning_rate * surprise_factor * confidence * 2.0
            new_theta = current_theta - theta_change
            
        # Update standard error (decreases with more items)
        new_se = current_se * 0.85  # Reduce SE by 15% each item
        
        # Bounds checking
        new_theta = max(-3.0, min(4.0, new_theta))  # Keep within reasonable bounds
        new_se = max(0.1, new_se)  # Minimum SE
        
        # Debug logging
        print(f"Theta update: {current_theta:.2f} -> {new_theta:.2f} (change: {new_theta-current_theta:+.2f})")
        print(f"  Item difficulty: {item_theta:.2f}, Correct: {is_correct}, Confidence: {confidence:.2f}")
        print(f"  Prob correct: {prob_correct:.2f}, SE: {current_se:.2f} -> {new_se:.2f}")
        
        return new_theta, new_se
    
    def should_stop(self, se: float, items_completed: int) -> bool:
        """Determine if testing should stop"""
        # Stop if SE is small enough and minimum items completed
        if se <= self.target_se and items_completed >= self.min_items:
            return True
            
        # Stop if maximum items reached
        if items_completed >= self.max_items:
            return True
            
        return False
    
    def get_final_cefr(self, theta: float) -> str:
        """Convert final theta to CEFR level"""
        # Find closest CEFR level
        closest_level = "B1"
        min_distance = float('inf')
        
        for cefr, cefr_theta in self.cefr_levels.items():
            distance = abs(theta - cefr_theta)
            if distance < min_distance:
                min_distance = distance
                closest_level = cefr
                
        return closest_level
    
    def get_confidence_interval(self, theta: float, se: float) -> Tuple[float, float]:
        """Get 95% confidence interval for ability estimate"""
        margin = 1.96 * se  # 95% CI
        return (theta - margin, theta + margin)
    
    def _probability_correct(self, theta: float, difficulty: float, discrimination: float = 1.0) -> float:
        """2PL IRT model: probability of correct response"""
        try:
            exponent = discrimination * (theta - difficulty)
            return 1 / (1 + math.exp(-exponent))
        except OverflowError:
            return 0.999 if exponent > 0 else 0.001
    
    def _item_information(self, theta: float, item_theta: float, discrimination: float = 1.5) -> float:
        """Fisher information for item at given ability level"""
        prob = self._probability_correct(theta, item_theta, discrimination)
        return discrimination**2 * prob * (1 - prob)
    
    def generate_known_words(self, cefr_level: str, language: str = 'en') -> List[str]:
        """Generate known word list based on CEFR level"""
        # Frequency-based word lists by CEFR level
        word_lists = {
            'A1': ['the', 'be', 'have', 'do', 'say', 'go', 'can', 'get', 'would', 'make', 
                   'know', 'will', 'think', 'take', 'see', 'come', 'could', 'want', 'look', 'use'],
            'A2': ['also', 'back', 'after', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
                   'any', 'these', 'give', 'day', 'most', 'us', 'is', 'water', 'than', 'call'],
            'B1': ['through', 'just', 'form', 'sentence', 'great', 'think', 'say', 'help', 'low', 'line',
                   'differ', 'turn', 'cause', 'much', 'mean', 'before', 'move', 'right', 'boy', 'old'],
            'B2': ['however', 'therefore', 'although', 'furthermore', 'nevertheless', 'consequently', 
                   'moreover', 'whereas', 'nonetheless', 'hence', 'thus', 'meanwhile', 'likewise'],
            'C1': ['notwithstanding', 'albeit', 'hitherto', 'erstwhile', 'ubiquitous', 'perspicacious',
                   'inexorable', 'surreptitious', 'serendipitous', 'magnanimous', 'ephemeral'],
            'C2': ['perspicacity', 'verisimilitude', 'pusillanimous', 'sesquipedalian', 'grandiloquent',
                   'obfuscation', 'recondite', 'abstruse', 'esoteric', 'arcane', 'ineffable']
        }
        
        # Include words from current level and all levels below
        known_words = []
        level_order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        current_index = level_order.index(cefr_level)
        
        for i in range(current_index + 1):
            level = level_order[i]
            known_words.extend(word_lists.get(level, []))
            
        return known_words
