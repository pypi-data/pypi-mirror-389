#!/usr/bin/env python3
"""
Comprehensive test for streaming with structured and unstructured outputs.
Tests both stream() and astream() methods for Gemini and OpenAI.
"""

import os
import asyncio
import pytest
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

from src.masai.GenerativeModel.vanilla_wrappers.gemini_wrapper import ChatGoogleGenerativeAI
from src.masai.GenerativeModel.vanilla_wrappers.openai_wrapper import ChatOpenAI


# ============================================================================
# TEST SCHEMAS
# ============================================================================

class SimpleResponse(BaseModel):
    """Simple structured output schema"""
    answer: str
    confidence: float


class DetailedResponse(BaseModel):
    """Detailed structured output schema"""
    reasoning: str
    answer: str
    confidence: float


# ============================================================================
# GEMINI TESTS
# ============================================================================

def test_gemini_stream_unstructured():
    """Test Gemini stream with unstructured output"""
    print("\n" + "="*60)
    print("TEST: Gemini stream (unstructured)")
    print("="*60)
    
    try:
        model = ChatGoogleGenerativeAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.5-flash",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        chunks = []
        for chunk in model.stream("What is 2+2?"):
            chunks.append(chunk)
            print(f"  Chunk: {chunk.content[:50]}...")
        
        print(f"[PASS] Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_gemini_stream_structured():
    """Test Gemini stream with structured output"""
    print("\n" + "="*60)
    print("TEST: Gemini stream (structured)")
    print("="*60)
    
    try:
        model = ChatGoogleGenerativeAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.5-flash",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        structured_model = model.with_structured_output(SimpleResponse)
        
        chunks = []
        final_response = None
        for chunk in structured_model.stream("What is 2+2?"):
            chunks.append(chunk)
            # Check if it's the final parsed response
            if hasattr(chunk, 'model_dump'):
                final_response = chunk
                print(f"  Final response: {chunk}")
            else:
                print(f"  Chunk: {chunk.content[:50]}...")
        
        if final_response:
            print(f"[PASS] Received {len(chunks)} chunks + final structured response")
            return True
        else:
            print(f"[FAIL] No final structured response received")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


@pytest.mark.asyncio
async def test_gemini_astream_unstructured():
    """Test Gemini astream with unstructured output"""
    print("\n" + "="*60)
    print("TEST: Gemini astream (unstructured)")
    print("="*60)
    
    try:
        model = ChatGoogleGenerativeAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.5-flash",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        chunks = []
        async for chunk in model.astream("What is 2+2?"):
            chunks.append(chunk)
            print(f"  Chunk: {chunk.content[:50]}...")
        
        print(f"[PASS] Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


@pytest.mark.asyncio
async def test_gemini_astream_structured():
    """Test Gemini astream with structured output"""
    print("\n" + "="*60)
    print("TEST: Gemini astream (structured)")
    print("="*60)
    
    try:
        model = ChatGoogleGenerativeAI(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-2.5-flash",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        structured_model = model.with_structured_output(SimpleResponse)
        
        chunks = []
        final_response = None
        async for chunk in structured_model.astream("What is 2+2?"):
            chunks.append(chunk)
            # Check if it's the final parsed response
            if hasattr(chunk, 'model_dump'):
                final_response = chunk
                print(f"  Final response: {chunk}")
            else:
                print(f"  Chunk: {chunk.content[:50]}...")
        
        if final_response:
            print(f"[PASS] Received {len(chunks)} chunks + final structured response")
            return True
        else:
            print(f"[FAIL] No final structured response received")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


# ============================================================================
# OPENAI TESTS
# ============================================================================

def test_openai_stream_unstructured():
    """Test OpenAI stream with unstructured output"""
    print("\n" + "="*60)
    print("TEST: OpenAI stream (unstructured)")
    print("="*60)
    
    try:
        model = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        chunks = []
        for chunk in model.stream("What is 2+2?"):
            chunks.append(chunk)
            print(f"  Chunk: {chunk.content[:50]}...")
        
        print(f"[PASS] Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_openai_stream_structured():
    """Test OpenAI stream with structured output"""
    print("\n" + "="*60)
    print("TEST: OpenAI stream (structured)")
    print("="*60)
    
    try:
        model = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        structured_model = model.with_structured_output(SimpleResponse)
        
        chunks = []
        final_response = None
        for chunk in structured_model.stream("What is 2+2?"):
            chunks.append(chunk)
            # Check if it's the final parsed response
            if hasattr(chunk, 'model_dump'):
                final_response = chunk
                print(f"  Final response: {chunk}")
            else:
                print(f"  Chunk: {chunk.content[:50]}...")
        
        if final_response:
            print(f"[PASS] Received {len(chunks)} chunks + final structured response")
            return True
        else:
            print(f"[FAIL] No final structured response received")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


@pytest.mark.asyncio
async def test_openai_astream_unstructured():
    """Test OpenAI astream with unstructured output"""
    print("\n" + "="*60)
    print("TEST: OpenAI astream (unstructured)")
    print("="*60)
    
    try:
        model = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        chunks = []
        async for chunk in model.astream("What is 2+2?"):
            chunks.append(chunk)
            print(f"  Chunk: {chunk.content[:50]}...")
        
        print(f"[PASS] Received {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


@pytest.mark.asyncio
async def test_openai_astream_structured():
    """Test OpenAI astream with structured output"""
    print("\n" + "="*60)
    print("TEST: OpenAI astream (structured)")
    print("="*60)
    
    try:
        model = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            temperature=0.7,
            max_output_tokens=256,
            verbose=False
        )
        
        structured_model = model.with_structured_output(SimpleResponse)
        
        chunks = []
        final_response = None
        async for chunk in structured_model.astream("What is 2+2?"):
            chunks.append(chunk)
            # Check if it's the final parsed response
            if hasattr(chunk, 'model_dump'):
                final_response = chunk
                print(f"  Final response: {chunk}")
            else:
                print(f"  Chunk: {chunk.content[:50]}...")
        
        if final_response:
            print(f"[PASS] Received {len(chunks)} chunks + final structured response")
            return True
        else:
            print(f"[FAIL] No final structured response received")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("STREAMING STRUCTURED OUTPUT TESTS")
    print("="*60)
    
    results = {}
    
    # Sync tests
    results["gemini_stream_unstructured"] = test_gemini_stream_unstructured()
    results["gemini_stream_structured"] = test_gemini_stream_structured()
    results["openai_stream_unstructured"] = test_openai_stream_unstructured()
    results["openai_stream_structured"] = test_openai_stream_structured()
    
    # Async tests
    results["gemini_astream_unstructured"] = await test_gemini_astream_unstructured()
    results["gemini_astream_structured"] = await test_gemini_astream_structured()
    results["openai_astream_unstructured"] = await test_openai_astream_unstructured()
    results["openai_astream_structured"] = await test_openai_astream_structured()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} passed")


if __name__ == "__main__":
    asyncio.run(main())

