#!/usr/bin/env python3
"""
Large Context Size Test for Ollama API Service
Tests performance and capabilities with varying context sizes
"""

import requests
import json
import time
import os
import statistics
from typing import Dict, Any, List, Tuple

# Configuration
OLLAMA_BASE_URL = "https://mlapi.us/vllm"  # Authenticated endpoint
OLLAMA_NATIVE_API = f"{OLLAMA_BASE_URL}/api"
OLLAMA_OPENAI_API = f"{OLLAMA_BASE_URL}/v1"
#DEFAULT_MODEL = "qwen3:30b-a3b-instruct-2507-q4_K_M"
#DEFAULT_MODEL = "gpt-oss:reasoning"  # 200K context model - ABSOLUTE MAXIMUM
DEFAULT_MODEL = "qwen3:200k"  # 200K context model - ABSOLUTE MAXIMUM
TIMEOUT = 600  # Extended timeout for very large context tests (10 minutes)

# API Key for authentication
API_KEY = "sk-ollama-368e69481eff6d9631b6a1f96deab3c2"

def get_headers():
    """Get headers for API requests"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

def analyze_failure(response, target_tokens):
    """Analyze failure response to determine the type of limit reached"""
    error_text = response.text[:500] if response.text else "No error message"
    print(f"📄 Error: {error_text}")
    
    # Check for specific error types that indicate limits
    if "out of memory" in error_text.lower() or "oom" in error_text.lower():
        print(f"💾 MEMORY LIMIT REACHED at {target_tokens:,} tokens!")
    elif "context" in error_text.lower() and ("limit" in error_text.lower() or "exceeded" in error_text.lower()):
        print(f"📏 CONTEXT WINDOW LIMIT EXCEEDED at {target_tokens:,} tokens!")
    elif "timeout" in error_text.lower():
        print(f"⏰ SERVER TIMEOUT at {target_tokens:,} tokens!")
    elif response.status_code == 413:
        print(f"📦 REQUEST TOO LARGE at {target_tokens:,} tokens!")
    elif response.status_code >= 500:
        print(f"🚨 SERVER ERROR at {target_tokens:,} tokens - possibly resource exhaustion!")
    elif response.status_code == 422:
        print(f"🔧 PROCESSING ERROR at {target_tokens:,} tokens - input validation failed!")
    else:
        print(f"❓ UNKNOWN FAILURE at {target_tokens:,} tokens - status {response.status_code}")

def generate_text_content(target_tokens: int) -> str:
    """Generate text content of approximately the specified number of tokens"""
    # Base content about Python programming
    base_content = """
Python is a high-level, interpreted programming language with dynamic semantics. 
Its high-level built-in data structures, combined with dynamic typing and dynamic binding, 
make it very attractive for Rapid Application Development, as well as for use as a scripting 
or glue language to connect existing components together. Python's simple, easy to learn 
syntax emphasizes readability and therefore reduces the cost of program maintenance. 
Python supports modules and packages, which encourages program modularity and code reuse.

Key features of Python include:
- Simple and easy to learn syntax
- Interpreted and interactive
- Object-oriented programming support
- Extensive standard library
- Cross-platform compatibility
- Large community and ecosystem
- Excellent for data science and machine learning
- Web development frameworks like Django and Flask
- Scientific computing with NumPy, SciPy, and Pandas
- Machine learning with TensorFlow, PyTorch, and scikit-learn

Python code examples:
def hello_world():
    print("Hello, World!")

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

# List comprehension
squares = [x**2 for x in range(10)]

# Dictionary comprehension
word_lengths = {word: len(word) for word in ["python", "programming", "language"]}

# Generator expression
even_numbers = (x for x in range(100) if x % 2 == 0)

# Context manager
with open("file.txt", "r") as f:
    content = f.read()

# Exception handling
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
finally:
    print("Cleanup code here")

# Decorators
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

@timing_decorator
def slow_function():
    time.sleep(1)
    return "Done"
"""
    
    # Estimate tokens: roughly 3.5 characters per token on average for English text
    avg_chars_per_token = 3.5
    target_chars = int(target_tokens * avg_chars_per_token)
    
    # Calculate how many repetitions we need to reach the target character count
    base_char_count = len(base_content)
    repetitions = max(1, target_chars // base_char_count)
    
    # Generate the content
    content = base_content * repetitions
    
    # Trim to approximate target character count (and thus token count)
    if len(content) > target_chars:
        content = content[:target_chars]
    
    return content

def test_context_size_native(target_tokens: int) -> Tuple[bool, float, int, int]:
    """
    Test native Ollama API with specified token count
    Returns: (success, response_time, prompt_tokens, completion_tokens)
    """
    print(f"🧪 Testing Native API with ~{target_tokens:,} token context...")
    
    large_content = generate_text_content(target_tokens)
    actual_size_kb = len(large_content.encode('utf-8')) / 1024
    estimated_tokens = len(large_content) / 3.5  # Rough estimate
    
    prompt = f"""Here is a large document about Python programming:

{large_content}

Based on this document, please provide a concise summary of the key Python features mentioned. Keep your response under 100 words."""
    
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 150
        }
    }
    
    try:
        print(f"📏 Estimated tokens: ~{estimated_tokens:,.0f} ({actual_size_kb:.1f}KB)")
        print("⏳ Sending request...")
        
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_NATIVE_API}/generate",
            json=payload,
            headers=get_headers(),
            timeout=TIMEOUT
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            # Extract token counts
            prompt_tokens = result.get('prompt_eval_count', 0)
            completion_tokens = result.get('eval_count', 0)
            
            print(f"✅ Success! Response time: {response_time:.2f}s")
            print(f"🔢 Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}")
            print(f"📝 Response preview: {response_text[:100]}...")
            
            # Calculate tokens per second
            if response_time > 0 and completion_tokens:
                tokens_per_sec = completion_tokens / response_time
                print(f"🚀 Tokens/second: {tokens_per_sec:.1f}")
            
            return True, response_time, prompt_tokens, completion_tokens
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"📄 Error: {response.text[:200]}")
            return False, response_time, 0, 0
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after {TIMEOUT}s")
        return False, TIMEOUT, 0, 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, 0, 0, 0

def test_context_size_openai(target_tokens: int) -> Tuple[bool, float, int, int]:
    """
    Test OpenAI compatible API with specified token count
    Returns: (success, response_time, prompt_tokens, completion_tokens)
    """
    print(f"🧪 Testing OpenAI API with ~{target_tokens:,} token context...")
    
    large_content = generate_text_content(target_tokens)
    actual_size_kb = len(large_content.encode('utf-8')) / 1024
    estimated_tokens = len(large_content) / 3.5  # Rough estimate
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can analyze and summarize documents."
        },
        {
            "role": "user",
            "content": f"""Here is a large document about Python programming:

{large_content}

Based on this document, please provide a concise summary of the key Python features mentioned. Keep your response under 100 words."""
        }
    ]
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.3,
        "stream": False
    }
    
    try:
        print(f"📏 Estimated tokens: ~{estimated_tokens:,.0f} ({actual_size_kb:.1f}KB)")
        print("⏳ Sending request...")
        
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_OPENAI_API}/chat/completions",
            json=payload,
            headers=get_headers(),
            timeout=TIMEOUT
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract response
            choice = result.get('choices', [{}])[0]
            message = choice.get('message', {})
            content = message.get('content', '')
            
            # Extract token counts
            usage = result.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            
            print(f"✅ Success! Response time: {response_time:.2f}s")
            print(f"🔢 Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}")
            print(f"📝 Response preview: {content[:100]}...")
            
            # Calculate tokens per second
            if response_time > 0 and completion_tokens:
                tokens_per_sec = completion_tokens / response_time
                print(f"🚀 Tokens/second: {tokens_per_sec:.1f}")
            
            return True, response_time, prompt_tokens, completion_tokens
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"📄 Error: {response.text[:200]}")
            return False, response_time, 0, 0
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after {TIMEOUT}s")
        return False, TIMEOUT, 0, 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, 0, 0, 0

def test_large_context_long_output() -> bool:
    """Test large context with long output generation"""
    print("\n📝 Testing Large Context + Long Output Generation...")
    
    # Test different combinations of context size and output length
    test_configs = [
        {"context": 50000, "max_tokens": 1000, "description": "50K context → 1K output"},
        {"context": 100000, "max_tokens": 2000, "description": "100K context → 2K output"},
        {"context": 150000, "max_tokens": 3000, "description": "150K context → 3K output"},
        {"context": 180000, "max_tokens": 4000, "description": "180K context → 4K output"},
        {"context": 200000, "max_tokens": 5000, "description": "200K context → 5K output"},
    ]
    
    for config in test_configs:
        print(f"\n🔥 {config['description']}")
        print("-" * 50)
        
        # Generate large input content
        large_content = generate_text_content(config["context"])
        actual_size_kb = len(large_content.encode('utf-8')) / 1024
        estimated_tokens = len(large_content) / 3.5
        
        print(f"📏 Input: ~{estimated_tokens:,.0f} tokens ({actual_size_kb:.1f}KB)")
        print(f"🎯 Target output: {config['max_tokens']:,} tokens")
        
        # Create a prompt that encourages long, detailed output
        prompt = f"""Here is a comprehensive Python programming document:

{large_content}

Based on this extensive document, please write a detailed, comprehensive tutorial about Python programming. Your response should be very thorough and include:

1. A complete introduction to Python and its philosophy
2. Detailed explanations of all major Python features mentioned
3. Extensive code examples with detailed explanations
4. Best practices and common pitfalls
5. Advanced topics and real-world applications
6. Performance considerations and optimization techniques
7. Ecosystem overview including popular libraries and frameworks

Please make your response as detailed and comprehensive as possible. Aim for a tutorial that could serve as a complete reference guide."""

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert Python instructor writing comprehensive educational content. Always provide detailed, thorough explanations with extensive examples."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            print("⏳ Generating long response...")
            start_time = time.time()
            response = requests.post(
                f"{OLLAMA_OPENAI_API}/chat/completions",
                json=payload,
                headers=get_headers(),
                timeout=TIMEOUT
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                choice = result.get('choices', [{}])[0]
                message = choice.get('message', {})
                content = message.get('content', '')
                
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = prompt_tokens + completion_tokens
                
                # Calculate output metrics
                output_chars = len(content)
                output_kb = output_chars / 1024
                
                print(f"✅ Success! Time: {response_time:.2f}s")
                print(f"📊 Tokens: {prompt_tokens:,} input + {completion_tokens:,} output = {total_tokens:,} total")
                print(f"📄 Output: {output_chars:,} characters ({output_kb:.1f}KB)")
                print(f"🚀 Speed: {completion_tokens/response_time:.1f} tokens/sec")
                print(f"💾 Total processing: {total_tokens:,} tokens")
                
                # Show preview of output
                preview_length = min(200, len(content))
                print(f"📝 Output preview: {content[:preview_length]}...")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"📄 Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True

def test_conversation_context() -> bool:
    """Test building up context through a long conversation"""
    print("\n🗣️ Testing Long Conversation Context...")
    
    conversation_history = [
        {"role": "system", "content": "You are a helpful Python programming tutor."},
        {"role": "user", "content": "Can you explain what Python is?"},
    ]
    
    # Simulate a long conversation by adding multiple exchanges
    topics = [
        "What are Python's main features?",
        "How do you handle exceptions in Python?",
        "Explain Python decorators with examples.",
        "What's the difference between lists and tuples?",
        "How does Python's garbage collection work?",
        "Explain Python's duck typing concept.",
        "What are Python generators and how do they work?",
        "Describe Python's Global Interpreter Lock (GIL).",
        "How do you optimize Python code performance?",
        "What are the best practices for Python project structure?"
    ]
    
    total_response_time = 0
    total_tokens = 0
    
    try:
        for i, topic in enumerate(topics, 1):
            print(f"  📝 Question {i}: {topic[:50]}...")
            
            # Add user question to conversation
            conversation_history.append({"role": "user", "content": topic})
            
            payload = {
                "model": DEFAULT_MODEL,
                "messages": conversation_history,
                "max_tokens": 200,
                "temperature": 0.7,
                "stream": False
            }
            
            start_time = time.time()
            response = requests.post(
                f"{OLLAMA_OPENAI_API}/chat/completions",
                json=payload,
                headers=get_headers(),
                timeout=TIMEOUT
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            total_response_time += response_time
            
            if response.status_code == 200:
                result = response.json()
                choice = result.get('choices', [{}])[0]
                message = choice.get('message', {})
                content = message.get('content', '')
                
                # Add assistant response to conversation history
                conversation_history.append({"role": "assistant", "content": content})
                
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens += prompt_tokens + completion_tokens
                
                print(f"    ✅ Response {i}: {response_time:.2f}s, {prompt_tokens + completion_tokens} tokens")
            else:
                print(f"    ❌ Failed at question {i}: {response.status_code}")
                return False
        
        context_size_kb = len(json.dumps(conversation_history).encode('utf-8')) / 1024
        print(f"  📊 Final conversation context: {context_size_kb:.1f}KB")
        print(f"  ⏱️ Total time: {total_response_time:.2f}s")
        print(f"  🔢 Total tokens processed: {total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Conversation test failed: {e}")
        return False

def run_context_size_benchmark():
    """Run comprehensive context size benchmarks"""
    print("🚀 Starting Large Context Size Benchmark")
    print("=" * 60)
    
    # Test different context sizes (in tokens) - FOCUSED ON LARGE CONTEXT + LONG OUTPUT
    context_sizes = [1000, 100000, 200000]
    
    native_results = []
    openai_results = []
    
    for target_tokens in context_sizes:
        print(f"\n📏 TESTING CONTEXT SIZE: {target_tokens:,} TOKENS")
        print("-" * 50)
        # IGNORE native testing for now
        # Test Native API
        #success, time_taken, prompt_tokens, completion_tokens = test_context_size_native(target_tokens)
        #native_results.append({
        #    'target_tokens': target_tokens,
        #    'success': success,
        #    'response_time': time_taken,
        #    'prompt_tokens': prompt_tokens,
        #    'completion_tokens': completion_tokens
        #})
        
        print()
        
        # Test OpenAI Compatible API
        success, time_taken, prompt_tokens, completion_tokens = test_context_size_openai(target_tokens)
        openai_results.append({
            'target_tokens': target_tokens,
            'success': success,
            'response_time': time_taken,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens
        })
        
        # If OpenAI API failed, we've likely hit the limit - stop testing
        if not success:
            print(f"\n🚨 OpenAI API failed at {target_tokens:,} tokens - likely reached hardware/model limit!")
            break
        
        # Small delay between tests
        time.sleep(2)
    
    # Test large context + long output generation
    print(f"\n🔥 LARGE CONTEXT + LONG OUTPUT TEST")
    print("-" * 50)
    long_output_success = test_large_context_long_output()
    
    # Test conversation context
    print(f"\n🗣️ CONVERSATION CONTEXT TEST")
    print("-" * 40)
    conversation_success = test_conversation_context()
    
    # Print summary
    print(f"\n" + "=" * 60)
    print("📊 LARGE CONTEXT TEST SUMMARY")
    print("=" * 60)
    
    print("\n🔧 NATIVE API RESULTS:")
    print("Target Tokens | Success | Time(s) | Actual Prompt Tokens | Completion Tokens")
    print("-" * 80)
    for result in native_results:
        status = "✅" if result['success'] else "❌"
        print(f"{result['target_tokens']:12,} | {status:7} | {result['response_time']:7.2f} | {result['prompt_tokens']:20,} | {result['completion_tokens']:17}")
    
    print("\n🔗 OPENAI API RESULTS:")
    print("Target Tokens | Success | Time(s) | Actual Prompt Tokens | Completion Tokens")
    print("-" * 80)
    for result in openai_results:
        status = "✅" if result['success'] else "❌"
        print(f"{result['target_tokens']:12,} | {status:7} | {result['response_time']:7.2f} | {result['prompt_tokens']:20,} | {result['completion_tokens']:17}")
    
    # Calculate statistics
    native_successful = [r for r in native_results if r['success']]
    openai_successful = [r for r in openai_results if r['success']]
    
    print("\n📈 PERFORMANCE ANALYSIS:")
    if native_successful:
        native_times = [r['response_time'] for r in native_successful]
        # Calculate tokens per second for successful tests
        native_tokens_per_sec = []
        for r in native_successful:
            if r['response_time'] > 0 and r['completion_tokens'] > 0:
                native_tokens_per_sec.append(r['completion_tokens'] / r['response_time'])
        
        print(f"Native API - Avg time: {statistics.mean(native_times):.2f}s, "
              f"Min: {min(native_times):.2f}s, Max: {max(native_times):.2f}s")
        if native_tokens_per_sec:
            print(f"Native API - Avg tokens/sec: {statistics.mean(native_tokens_per_sec):.1f}, "
                  f"Min: {min(native_tokens_per_sec):.1f}, Max: {max(native_tokens_per_sec):.1f}")
    
    if openai_successful:
        openai_times = [r['response_time'] for r in openai_successful]
        # Calculate tokens per second for successful tests
        openai_tokens_per_sec = []
        for r in openai_successful:
            if r['response_time'] > 0 and r['completion_tokens'] > 0:
                openai_tokens_per_sec.append(r['completion_tokens'] / r['response_time'])
        
        print(f"OpenAI API - Avg time: {statistics.mean(openai_times):.2f}s, "
              f"Min: {min(openai_times):.2f}s, Max: {max(openai_times):.2f}s")
        if openai_tokens_per_sec:
            print(f"OpenAI API - Avg tokens/sec: {statistics.mean(openai_tokens_per_sec):.1f}, "
                  f"Min: {min(openai_tokens_per_sec):.1f}, Max: {max(openai_tokens_per_sec):.1f}")
    
    # Find maximum successful context size
    max_native_tokens = max([r['target_tokens'] for r in native_successful]) if native_successful else 0
    max_openai_tokens = max([r['target_tokens'] for r in openai_successful]) if openai_successful else 0
    
    print(f"\n🎯 MAXIMUM CONTEXT SIZES:")
    print(f"Native API: {max_native_tokens:,} tokens")
    print(f"OpenAI API: {max_openai_tokens:,} tokens")
    print(f"Long Output Test: {'✅ Success' if long_output_success else '❌ Failed'}")
    print(f"Conversation Test: {'✅ Success' if conversation_success else '❌ Failed'}")
    
    # Success rate
    if len(native_results) > 0:
        native_success_rate = len(native_successful) / len(native_results) * 100
    else:
        native_success_rate = 0
    
    if len(openai_results) > 0:
        openai_success_rate = len(openai_successful) / len(openai_results) * 100
    else:
        openai_success_rate = 0
    
    print(f"\n📊 SUCCESS RATES:")
    print(f"Native API: {native_success_rate:.1f}% ({len(native_successful)}/{len(native_results)})")
    print(f"OpenAI API: {openai_success_rate:.1f}% ({len(openai_successful)}/{len(openai_results)})")

def main():
    """Main test function"""
    print("🧪 Large Context Token Limit Test for Ollama API Service - Testing up to 200k tokens")
    print("=" * 80)
    print(f"🔗 Native API Base URL: {OLLAMA_NATIVE_API}")
    print(f"🔗 OpenAI Compatible API Base URL: {OLLAMA_OPENAI_API}")
    print(f"🤖 Model: {DEFAULT_MODEL}")
    print(f"⏰ Timeout: {TIMEOUT}s")
    print(f"🔐 Authentication: Bearer API Key")
    print(f"🔑 API Key: {API_KEY[:20]}...{API_KEY[-8:]}")
    print("=" * 60)
    
    # Quick health check first
    try:
        response = requests.get(f"{OLLAMA_NATIVE_API}/tags", timeout=10, headers=get_headers())
        if response.status_code != 200:
            print("❌ Ollama service is not accessible!")
            print("💡 Make sure the ollama_api container is running:")
            print("💡 docker compose up -d ollama_api")
            return
    except Exception as e:
        print(f"❌ Ollama service check failed: {e}")
        return
    
    print("✅ Ollama service is accessible, starting context size tests...")
    
    # Run the benchmark
    run_context_size_benchmark()
    
    print(f"\n🎉 Large context token limit testing completed!")
    print(f"🔗 Tested endpoint: {OLLAMA_BASE_URL}")
    print(f"📊 Maximum tested: 200,000 tokens")

if __name__ == "__main__":
    main()