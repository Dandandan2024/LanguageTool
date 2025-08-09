"""
Contextual Learning Credit Distribution
When user reviews a sentence, distribute learning credit to all words intelligently
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class CreditType(Enum):
    PRIMARY = "primary"      # Target word gets full credit
    SUPPORTING = "supporting"  # Other content words get partial credit  
    STRUCTURAL = "structural"  # Grammar words get minimal credit
    IGNORED = "ignored"      # Very basic words get no credit

@dataclass
class WordCredit:
    word: str
    lexeme_id: str
    credit_type: CreditType
    credit_multiplier: float  # 0.0 to 1.0
    adjusted_rating: int     # Final rating after adjustment

def analyze_sentence_words(sentence: str, target_word: str, user_cefr: str) -> List[str]:
    """
    Extract meaningful words from sentence (excluding punctuation, basic particles)
    In production, this would use proper Russian tokenization
    """
    # Simple tokenization for demo (would use proper Russian NLP)
    words = sentence.lower().replace('.', '').replace(',', '').split()
    
    # Filter out very basic structural words that don't need credit
    basic_words = {'я', 'ты', 'он', 'она', 'мы', 'вы', 'они', 'в', 'на', 'и', 'а', 'но'}
    
    return [word for word in words if word not in basic_words]

def classify_word_importance(word: str, target_word: str, user_cefr: str, word_frequency: int = None) -> CreditType:
    """
    Classify how much credit each word should receive
    """
    if word == target_word:
        return CreditType.PRIMARY
    
    # Very high frequency words (top 100) get minimal credit for advanced users
    if word_frequency and word_frequency <= 100 and user_cefr in ['B2', 'C1', 'C2']:
        return CreditType.STRUCTURAL
    
    # Grammar particles, prepositions, etc.
    structural_words = {'не', 'то', 'это', 'что', 'как', 'где', 'когда', 'почему'}
    if word in structural_words:
        return CreditType.STRUCTURAL
    
    # Content words get supporting credit
    return CreditType.SUPPORTING

def calculate_credit_multiplier(credit_type: CreditType, user_rating: int, user_cefr: str) -> float:
    """
    Calculate how much credit to give based on word type and user rating
    """
    base_multipliers = {
        CreditType.PRIMARY: 1.0,      # Full credit
        CreditType.SUPPORTING: 0.6,   # 60% credit
        CreditType.STRUCTURAL: 0.2,   # 20% credit
        CreditType.IGNORED: 0.0       # No credit
    }
    
    base_multiplier = base_multipliers[credit_type]
    
    # Adjust based on user rating and difficulty
    if user_rating == 1:  # Again - user struggled
        # Don't give much credit to supporting words if they struggled
        if credit_type == CreditType.SUPPORTING:
            base_multiplier *= 0.3  # Reduce to 18% credit
        elif credit_type == CreditType.STRUCTURAL:
            base_multiplier = 0.0   # No credit for structural words
            
    elif user_rating == 4:  # Easy - user found it simple
        # Give more generous credit to supporting words
        if credit_type == CreditType.SUPPORTING:
            base_multiplier *= 1.2  # Increase to 72% credit (capped at 1.0)
    
    return min(1.0, base_multiplier)

def adjust_rating_for_word(base_rating: int, credit_multiplier: float, credit_type: CreditType) -> int:
    """
    Convert user's rating for target word into appropriate rating for supporting words
    """
    if credit_type == CreditType.PRIMARY:
        return base_rating  # Target word keeps original rating
    
    if credit_multiplier == 0.0:
        return None  # No review needed
    
    # Conservative approach for supporting words
    if base_rating == 1:  # Again
        return 1  # Supporting words also marked as "Again" (but with less impact)
    elif base_rating == 2:  # Hard  
        return 2  # Supporting words also "Hard"
    elif base_rating == 3:  # Good
        return 3  # Supporting words get "Good" 
    else:  # Easy (4)
        return 3  # Supporting words get "Good" (not Easy - be conservative)

def distribute_contextual_credit(
    sentence: str, 
    target_word: str, 
    user_rating: int, 
    user_cefr: str,
    word_lexeme_map: Dict[str, str] = None
) -> List[WordCredit]:
    """
    Main function: distribute learning credit across all words in sentence
    """
    if not word_lexeme_map:
        word_lexeme_map = {}  # Would be populated from database
    
    # Extract meaningful words
    words = analyze_sentence_words(sentence, target_word, user_cefr)
    
    credit_distribution = []
    
    for word in words:
        # Classify word importance
        credit_type = classify_word_importance(word, target_word, user_cefr)
        
        # Skip if no credit needed
        if credit_type == CreditType.IGNORED:
            continue
            
        # Calculate credit multiplier
        credit_multiplier = calculate_credit_multiplier(credit_type, user_rating, user_cefr)
        
        # Skip if no credit after adjustments
        if credit_multiplier == 0.0:
            continue
            
        # Adjust rating for this word
        adjusted_rating = adjust_rating_for_word(user_rating, credit_multiplier, credit_type)
        
        if adjusted_rating is None:
            continue
            
        lexeme_id = word_lexeme_map.get(word, f"unknown_{word}")
        
        credit_distribution.append(WordCredit(
            word=word,
            lexeme_id=lexeme_id,
            credit_type=credit_type,
            credit_multiplier=credit_multiplier,
            adjusted_rating=adjusted_rating
        ))
    
    return credit_distribution

# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        {
            "sentence": "Я хочу есть гамбургер",
            "target_word": "есть", 
            "user_rating": 4,
            "user_cefr": "B1"
        },
        {
            "sentence": "Моя мать читает интересную книгу",
            "target_word": "читает",
            "user_rating": 2, 
            "user_cefr": "A2"
        },
        {
            "sentence": "В красивом доме живут счастливые люди",
            "target_word": "доме",
            "user_rating": 1,
            "user_cefr": "B2"  
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}:")
        print(f"Sentence: {test['sentence']}")
        print(f"Target: {test['target_word']} | Rating: {test['user_rating']} | CEFR: {test['user_cefr']}")
        
        credits = distribute_contextual_credit(
            test['sentence'],
            test['target_word'], 
            test['user_rating'],
            test['user_cefr']
        )
        
        print("📊 Credit Distribution:")
        for credit in credits:
            print(f"  {credit.word}: {credit.credit_type.value} | "
                  f"×{credit.credit_multiplier:.1f} | rating {credit.adjusted_rating}")
