"""
LLM Content Generation Service
Generates Russian language learning content using OpenAI API with CEFR constraints
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import openai
import psycopg2
from psycopg2.extras import RealDictCursor

# OpenAI client will be initialized in ContentGenerator class

class ContentType(Enum):
    VOCABULARY = "vocabulary"
    SENTENCE = "sentence" 
    CLOZE = "cloze"

class CEFRLevel(Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

@dataclass
class GenerationRequest:
    target_word: str
    target_lexeme_id: str
    content_type: ContentType
    user_cefr: CEFRLevel
    user_id: str
    context_hint: Optional[str] = None
    avoid_words: Optional[List[str]] = None  # Words user doesn't know yet

@dataclass
class GeneratedContent:
    content_type: ContentType
    question_text: str
    answer_text: str
    target_word: str
    difficulty_theta: float
    supporting_words: List[str]
    metadata: Dict

class ContentGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        openai.api_key = api_key
    
    async def generate_content(self, request: GenerationRequest) -> GeneratedContent:
        """Main content generation method"""
        
        # Get CEFR-appropriate vocabulary constraints
        vocab_constraints = await self._get_cefr_vocabulary_constraints(request.user_cefr)
        
        # Generate prompt based on content type
        if request.content_type == ContentType.VOCABULARY:
            return await self._generate_vocabulary_card(request, vocab_constraints)
        elif request.content_type == ContentType.SENTENCE:
            return await self._generate_sentence_card(request, vocab_constraints)
        elif request.content_type == ContentType.CLOZE:
            return await self._generate_cloze_card(request, vocab_constraints)
        else:
            raise ValueError(f"Unsupported content type: {request.content_type}")
    
    async def _get_cefr_vocabulary_constraints(self, cefr_level: CEFRLevel) -> Dict:
        """Get vocabulary constraints for CEFR level"""
        
        # CEFR level to theta mapping
        cefr_theta_map = {
            CEFRLevel.A1: -2.0,
            CEFRLevel.A2: -1.0, 
            CEFRLevel.B1: 0.0,
            CEFRLevel.B2: 1.0,
            CEFRLevel.C1: 2.0,
            CEFRLevel.C2: 3.0
        }
        
        target_theta = cefr_theta_map[cefr_level]
        
        # Get common words at this level from our database
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT lemma, frequency_rank, cefr_level
                    FROM lexemes 
                    WHERE language = 'ru' 
                    AND cefr_level IN (%s, %s)
                    AND frequency_rank <= 2000
                    ORDER BY frequency_rank ASC
                    LIMIT 200
                """, (cefr_level.value, self._get_lower_cefr_level(cefr_level)))
                
                allowed_words = [row['lemma'] for row in cur.fetchall()]
        except:
            # Fallback if lexemes table not populated yet
            allowed_words = self._get_fallback_vocabulary(cefr_level)
        
        return {
            "target_theta": target_theta,
            "allowed_words": allowed_words,
            "max_sentence_length": self._get_max_sentence_length(cefr_level),
            "complexity_guidelines": self._get_complexity_guidelines(cefr_level)
        }
    
    def _get_lower_cefr_level(self, level: CEFRLevel) -> str:
        """Get the CEFR level below the current one"""
        levels = [CEFRLevel.A1, CEFRLevel.A2, CEFRLevel.B1, CEFRLevel.B2, CEFRLevel.C1, CEFRLevel.C2]
        try:
            current_index = levels.index(level)
            if current_index > 0:
                return levels[current_index - 1].value
        except:
            pass
        return CEFRLevel.A1.value
    
    def _get_max_sentence_length(self, cefr_level: CEFRLevel) -> int:
        """Get maximum sentence length for CEFR level"""
        length_map = {
            CEFRLevel.A1: 6,
            CEFRLevel.A2: 8,
            CEFRLevel.B1: 12,
            CEFRLevel.B2: 15,
            CEFRLevel.C1: 20,
            CEFRLevel.C2: 25
        }
        return length_map[cefr_level]
    
    def _get_complexity_guidelines(self, cefr_level: CEFRLevel) -> str:
        """Get complexity guidelines for CEFR level"""
        guidelines = {
            CEFRLevel.A1: "Use present tense, basic vocabulary, simple sentence structure",
            CEFRLevel.A2: "Use present/past tense, common vocabulary, simple compound sentences",
            CEFRLevel.B1: "Use various tenses, intermediate vocabulary, some complex sentences",
            CEFRLevel.B2: "Use all tenses, advanced vocabulary, complex sentence structures",
            CEFRLevel.C1: "Use sophisticated vocabulary, complex grammar, nuanced expressions",
            CEFRLevel.C2: "Use native-level vocabulary, complex grammar, idiomatic expressions"
        }
        return guidelines[cefr_level]
    
    def _get_fallback_vocabulary(self, cefr_level: CEFRLevel) -> List[str]:
        """Fallback vocabulary lists if database not populated"""
        vocab_lists = {
            CEFRLevel.A1: ["я", "ты", "он", "она", "дом", "есть", "пить", "хотеть", "идти", "видеть"],
            CEFRLevel.A2: ["работать", "учиться", "читать", "писать", "говорить", "слушать", "думать"],
            CEFRLevel.B1: ["изучать", "понимать", "объяснять", "рассказывать", "спрашивать"],
            CEFRLevel.B2: ["анализировать", "сравнивать", "обсуждать", "предлагать"],
            CEFRLevel.C1: ["исследовать", "анализировать", "синтезировать"],
            CEFRLevel.C2: ["концептуализировать", "систематизировать"]
        }
        
        # Include all lower levels
        result = []
        levels = [CEFRLevel.A1, CEFRLevel.A2, CEFRLevel.B1, CEFRLevel.B2, CEFRLevel.C1, CEFRLevel.C2]
        current_index = levels.index(cefr_level)
        
        for i in range(current_index + 1):
            result.extend(vocab_lists[levels[i]])
        
        return result
    
    async def _generate_vocabulary_card(self, request: GenerationRequest, constraints: Dict) -> GeneratedContent:
        """Generate a vocabulary card with definition and example"""
        
        prompt = f"""Create a Russian vocabulary card for "{request.target_word}". Respond ONLY in JSON format.

{{
    "question_text": "Russian definition using simple words",
    "answer_text": "Example sentence with {request.target_word}",
    "target_word": "{request.target_word}",
    "difficulty_explanation": "Why appropriate for {request.user_cefr.value}",
    "supporting_words": ["word1", "word2", "word3"]
}}"""

        # GPT-5 models don't support max_tokens or custom temperature
        if self.model.startswith("gpt-5"):
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
        else:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
        
        try:
            raw_response = response.choices[0].message['content'].strip()
            print(f"🤖 Raw OpenAI Response: {raw_response}")  # Debug print
            
            # Remove markdown code blocks if present
            if raw_response.startswith('```json'):
                raw_response = raw_response[7:]  # Remove ```json
            if raw_response.endswith('```'):
                raw_response = raw_response[:-3]  # Remove ```
            raw_response = raw_response.strip()
            
            result = json.loads(raw_response)
            
            return GeneratedContent(
                content_type=ContentType.VOCABULARY,
                question_text=result["question_text"],
                answer_text=result["answer_text"],
                target_word=request.target_word,
                difficulty_theta=constraints["target_theta"],
                supporting_words=result.get("supporting_words", []),
                metadata={
                    "cefr_level": request.user_cefr.value,
                    "generation_method": "llm_vocabulary",
                    "difficulty_explanation": result.get("difficulty_explanation", "")
                }
            )
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"❌ Raw response was: {raw_response}")
            raise ValueError(f"Failed to parse LLM response as JSON: {raw_response[:200]}")
    
    async def _generate_sentence_card(self, request: GenerationRequest, constraints: Dict) -> GeneratedContent:
        """Generate a sentence translation card"""
        
        prompt = f"""Create a Russian sentence translation exercise featuring the word "{request.target_word}".

Target CEFR Level: {request.user_cefr.value}
Complexity Guidelines: {constraints['complexity_guidelines']}
Max Sentence Length: {constraints['max_sentence_length']} words

Requirements:
1. Create a natural Russian sentence using "{request.target_word}"
2. Keep the sentence under {constraints['max_sentence_length']} words
3. Use vocabulary appropriate for {request.user_cefr.value} level
4. Make the sentence practical and realistic
5. Ensure the target word is essential to the meaning

Format your response as JSON:
{{
    "question_text": "Russian sentence to translate",
    "answer_text": "English translation of the sentence",
    "target_word": "{request.target_word}",
    "difficulty_explanation": "Why this sentence is appropriate for {request.user_cefr.value}",
    "supporting_words": ["list", "of", "other", "key", "words", "in", "sentence"]
}}"""

        # GPT-5 models don't support max_tokens or custom temperature
        if self.model.startswith("gpt-5"):
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
        else:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
        
        try:
            result = json.loads(response.choices[0].message['content'])
            
            return GeneratedContent(
                content_type=ContentType.SENTENCE,
                question_text=result["question_text"],
                answer_text=result["answer_text"],
                target_word=request.target_word,
                difficulty_theta=constraints["target_theta"],
                supporting_words=result.get("supporting_words", []),
                metadata={
                    "cefr_level": request.user_cefr.value,
                    "generation_method": "llm_sentence",
                    "difficulty_explanation": result.get("difficulty_explanation", "")
                }
            )
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response as JSON")
    
    async def _generate_cloze_card(self, request: GenerationRequest, constraints: Dict) -> GeneratedContent:
        """Generate a cloze (fill-in-the-blank) card"""
        
        prompt = f"""Create a Russian cloze exercise (fill-in-the-blank) featuring the word "{request.target_word}".

Target CEFR Level: {request.user_cefr.value}
Complexity Guidelines: {constraints['complexity_guidelines']}
Max Sentence Length: {constraints['max_sentence_length']} words

Requirements:
1. Create a natural Russian sentence using "{request.target_word}"
2. Replace "{request.target_word}" with "___" to create the cloze
3. Keep the sentence under {constraints['max_sentence_length']} words
4. Use vocabulary appropriate for {request.user_cefr.value} level
5. Make sure the context clearly indicates the target word

Format your response as JSON:
{{
    "question_text": "Russian sentence with ___ replacing the target word",
    "answer_text": "{request.target_word}",
    "target_word": "{request.target_word}",
    "difficulty_explanation": "Why this cloze is appropriate for {request.user_cefr.value}",
    "supporting_words": ["list", "of", "other", "key", "words", "in", "sentence"]
}}"""

        # GPT-5 models don't support max_tokens or custom temperature
        if self.model.startswith("gpt-5"):
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
        else:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
        
        try:
            result = json.loads(response.choices[0].message['content'])
            
            return GeneratedContent(
                content_type=ContentType.CLOZE,
                question_text=result["question_text"],
                answer_text=result["answer_text"],
                target_word=request.target_word,
                difficulty_theta=constraints["target_theta"],
                supporting_words=result.get("supporting_words", []),
                metadata={
                    "cefr_level": request.user_cefr.value,
                    "generation_method": "llm_cloze",
                    "difficulty_explanation": result.get("difficulty_explanation", "")
                }
            )
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response as JSON")

# Utility functions for database integration
async def save_generated_content(content: GeneratedContent, db_connection, user_id: str) -> str:
    """Save generated content to database and return card ID"""
    
    with db_connection.cursor(cursor_factory=RealDictCursor) as cur:
        # Insert into cards table
        card_payload = {
            "question": content.question_text,
            "answer": content.answer_text,
            "target_word": content.target_word,
            "theta": content.difficulty_theta,
            "supporting_words": content.supporting_words,
            "generation_metadata": content.metadata
        }
        
        cur.execute("""
            INSERT INTO cards (type, language, payload)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (content.content_type.value, "ru", json.dumps(card_payload)))
        
        card_id = cur.fetchone()["id"]
        
        # Log the generation
        cur.execute("""
            INSERT INTO content_generation_log (
                user_id, card_id, target_word, content_type, 
                cefr_level, generation_method, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, (
            user_id, str(card_id), content.target_word, 
            content.content_type.value, content.metadata.get("cefr_level"),
            content.metadata.get("generation_method")
        ))
        
        db_connection.commit()
        return str(card_id)

# Example usage and testing
async def test_content_generation():
    """Test the content generation system"""
    
    # Mock database connection for testing
    import psycopg2
    from dotenv import load_dotenv
    
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
        generator = ContentGenerator(conn)
        
        # Test vocabulary card
        vocab_request = GenerationRequest(
            target_word="читать",
            target_lexeme_id="lexeme_123",
            content_type=ContentType.VOCABULARY,
            user_cefr=CEFRLevel.B1,
            user_id="test_user"
        )
        
        print("🧪 Testing Vocabulary Card Generation...")
        vocab_content = await generator.generate_content(vocab_request)
        print(f"Question: {vocab_content.question_text}")
        print(f"Answer: {vocab_content.answer_text}")
        print(f"Supporting words: {vocab_content.supporting_words}")
        print()
        
        # Test sentence card
        sentence_request = GenerationRequest(
            target_word="изучать",
            target_lexeme_id="lexeme_456",
            content_type=ContentType.SENTENCE,
            user_cefr=CEFRLevel.B2,
            user_id="test_user"
        )
        
        print("🧪 Testing Sentence Card Generation...")
        sentence_content = await generator.generate_content(sentence_request)
        print(f"Question: {sentence_content.question_text}")
        print(f"Answer: {sentence_content.answer_text}")
        print(f"Supporting words: {sentence_content.supporting_words}")
        print()
        
        # Test cloze card
        cloze_request = GenerationRequest(
            target_word="понимать",
            target_lexeme_id="lexeme_789",
            content_type=ContentType.CLOZE,
            user_cefr=CEFRLevel.A2,
            user_id="test_user"
        )
        
        print("🧪 Testing Cloze Card Generation...")
        cloze_content = await generator.generate_content(cloze_request)
        print(f"Question: {cloze_content.question_text}")
        print(f"Answer: {cloze_content.answer_text}")
        print(f"Supporting words: {cloze_content.supporting_words}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_content_generation())
