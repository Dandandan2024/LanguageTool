"""
API endpoints for LLM content generation
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
import asyncio
import json
from datetime import datetime

from .content_generator import (
    ContentGenerator, GenerationRequest, ContentType, CEFRLevel,
    save_generated_content
)

# Pydantic models for API requests/responses
class GenerateContentRequest(BaseModel):
    target_word: str
    content_type: Literal["vocabulary", "sentence", "cloze"]
    user_cefr: Literal["A1", "A2", "B1", "B2", "C1", "C2"] = "B1"
    user_id: str = "anonymous"
    context_hint: Optional[str] = None
    avoid_words: Optional[List[str]] = None

class GeneratedContentResponse(BaseModel):
    success: bool
    card_id: str
    content_type: str
    question_text: str
    answer_text: str
    target_word: str
    difficulty_theta: float
    supporting_words: List[str]
    metadata: dict
    generation_time_ms: int

class BatchGenerateRequest(BaseModel):
    target_words: List[str]
    content_type: Literal["vocabulary", "sentence", "cloze"]
    user_cefr: Literal["A1", "A2", "B1", "B2", "C1", "C2"] = "B1"
    user_id: str = "anonymous"
    max_concurrent: int = 3

class BatchGenerateResponse(BaseModel):
    success: bool
    generated_count: int
    failed_count: int
    card_ids: List[str]
    errors: List[str]
    total_time_ms: int

async def generate_single_content(request: GenerateContentRequest, db_connection) -> GeneratedContentResponse:
    """Generate a single piece of content"""
    
    start_time = datetime.now()
    
    try:
        # Create generator
        generator = ContentGenerator(db_connection)
        
        # Create generation request
        gen_request = GenerationRequest(
            target_word=request.target_word,
            target_lexeme_id=f"temp_{request.target_word}",  # Would lookup real lexeme_id
            content_type=ContentType(request.content_type),
            user_cefr=CEFRLevel(request.user_cefr),
            user_id=request.user_id,
            context_hint=request.context_hint,
            avoid_words=request.avoid_words
        )
        
        # Generate content
        content = await generator.generate_content(gen_request)
        
        # Save to database
        card_id = await save_generated_content(content, db_connection, request.user_id)
        
        # Calculate generation time
        generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return GeneratedContentResponse(
            success=True,
            card_id=card_id,
            content_type=content.content_type.value,
            question_text=content.question_text,
            answer_text=content.answer_text,
            target_word=content.target_word,
            difficulty_theta=content.difficulty_theta,
            supporting_words=content.supporting_words,
            metadata=content.metadata,
            generation_time_ms=generation_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

async def generate_batch_content(request: BatchGenerateRequest, db_connection) -> BatchGenerateResponse:
    """Generate multiple pieces of content in parallel"""
    
    start_time = datetime.now()
    
    try:
        # Create individual requests
        individual_requests = []
        for word in request.target_words:
            individual_requests.append(GenerateContentRequest(
                target_word=word,
                content_type=request.content_type,
                user_cefr=request.user_cefr,
                user_id=request.user_id
            ))
        
        # Process in batches to avoid overwhelming the API
        results = []
        errors = []
        
        for i in range(0, len(individual_requests), request.max_concurrent):
            batch = individual_requests[i:i + request.max_concurrent]
            
            # Process batch concurrently
            batch_tasks = [
                generate_single_content(req, db_connection) 
                for req in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                else:
                    results.append(result)
        
        # Calculate total time
        total_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return BatchGenerateResponse(
            success=len(errors) == 0,
            generated_count=len(results),
            failed_count=len(errors),
            card_ids=[r.card_id for r in results],
            errors=errors,
            total_time_ms=total_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")

async def get_generation_suggestions(user_cefr: str, user_id: str, db_connection, limit: int = 10) -> List[str]:
    """Get suggested words for content generation based on user's learning progress"""
    
    try:
        from psycopg2.extras import RealDictCursor
        
        with db_connection.cursor(cursor_factory=RealDictCursor) as cur:
            # CEFR level to theta mapping
            cefr_theta_map = {"A1": -2.0, "A2": -1.0, "B1": 0.0, "B2": 1.0, "C1": 2.0, "C2": 3.0}
            target_theta = cefr_theta_map.get(user_cefr, 0.0)
            
            # Find words the user hasn't seen yet or struggled with
            cur.execute("""
                SELECT l.lemma, l.frequency_rank, l.cefr_level
                FROM lexemes l
                LEFT JOIN user_lexemes ul ON l.id = ul.lexeme_id AND ul.user_id = %s
                WHERE l.language = 'ru'
                AND l.cefr_level = %s
                AND (ul.lexeme_id IS NULL OR ul.stability < 2.0)
                ORDER BY l.frequency_rank ASC
                LIMIT %s
            """, (user_id, user_cefr, limit))
            
            suggestions = [row['lemma'] for row in cur.fetchall()]
            
            # If not enough suggestions, fall back to common words
            if len(suggestions) < limit:
                fallback_words = {
                    "A1": ["есть", "пить", "идти", "видеть", "хотеть", "жить", "работать"],
                    "A2": ["читать", "писать", "говорить", "слушать", "думать", "знать"],
                    "B1": ["изучать", "понимать", "объяснять", "рассказывать", "спрашивать"],
                    "B2": ["анализировать", "сравнивать", "обсуждать", "предлагать"],
                    "C1": ["исследовать", "анализировать", "синтезировать"],
                    "C2": ["концептуализировать", "систематизировать"]
                }
                
                suggestions.extend(fallback_words.get(user_cefr, fallback_words["B1"]))
                suggestions = list(set(suggestions))[:limit]  # Remove duplicates and limit
            
            return suggestions
            
    except Exception as e:
        # Fallback suggestions if database query fails
        fallback = {
            "A1": ["дом", "есть", "пить", "идти", "видеть"],
            "A2": ["читать", "писать", "говорить", "думать", "знать"],
            "B1": ["изучать", "понимать", "объяснять", "работать"],
            "B2": ["анализировать", "сравнивать", "обсуждать"],
            "C1": ["исследовать", "синтезировать"],
            "C2": ["концептуализировать"]
        }
        return fallback.get(user_cefr, fallback["B1"])[:limit]
