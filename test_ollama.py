#!/usr/bin/env python3
"""
Test script for the Ollama API service
Tests both native Ollama API and OpenAI compatible endpoints
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
OLLAMA_BASE_URL = "http://localhost:8080"  # From docker-compose.yaml
OLLAMA_NATIVE_API = f"{OLLAMA_BASE_URL}/api"
OLLAMA_OPENAI_API = f"{OLLAMA_BASE_URL}/v1" 
DEFAULT_MODEL = "qwen3:262k"  # From start.sh
TIMEOUT = 120

def get_headers():
    """Get headers for API requests"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def test_ollama_health():
    """Test if Ollama service is accessible"""
    print("🔍 Testing Ollama service health...")
    try:
        # Test with the tags endpoint since Ollama doesn't have a dedicated health endpoint
        response = requests.get(f"{OLLAMA_NATIVE_API}/tags", timeout=10, headers=get_headers())
        print(f"✅ Ollama service accessible: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ollama health check failed: {e}")
        return False

def test_native_ollama_list_models():
    """Test native Ollama API list models endpoint"""
    print("\n📋 Testing Native Ollama API - List Models...")
    try:
        response = requests.get(f"{OLLAMA_NATIVE_API}/tags", timeout=30, headers=get_headers())
        
        if response.status_code == 200:
            models_data = response.json()
            print(f"✅ Native models endpoint working!")
            
            models = models_data.get('models', [])
            print(f"📊 Available models ({len(models)}):")
            for model in models:
                model_name = model.get('name', 'Unknown')
                model_size = model.get('size', 'Unknown')
                modified_at = model.get('modified_at', 'Unknown')
                print(f"   - {model_name} (size: {model_size}, modified: {modified_at[:19] if modified_at != 'Unknown' else 'Unknown'})")
            
            return len(models) > 0
        else:
            print(f"❌ Native models endpoint failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Native models listing failed: {e}")
        return False

def test_openai_compatible_models():
    """Test OpenAI compatible models endpoint"""
    print("\n📋 Testing OpenAI Compatible API - List Models...")
    try:
        response = requests.get(f"{OLLAMA_OPENAI_API}/models", timeout=30, headers=get_headers())
        
        if response.status_code == 200:
            models_data = response.json()
            print(f"✅ OpenAI compatible models endpoint working!")
            
            models = models_data.get('data', [])
            print(f"📊 Available models ({len(models)}):")
            for model in models:
                model_id = model.get('id', 'Unknown')
                model_object = model.get('object', 'Unknown')
                created = model.get('created', 'Unknown')
                print(f"   - {model_id} (type: {model_object}, created: {created})")
            
            return len(models) > 0
        else:
            print(f"❌ OpenAI compatible models endpoint failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI compatible models listing failed: {e}")
        return False

def test_native_ollama_generate():
    """Test native Ollama generate endpoint"""
    print(f"\n🧪 Testing Native Ollama API - Generate with model: {DEFAULT_MODEL}")
    
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": "Write a simple Python function to calculate the factorial of a number. Keep it concise.",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 500
        }
    }
    
    try:
        print("⏳ Sending generate request...")
        start_time = time.time()
        
        response = requests.post(
            f"{OLLAMA_NATIVE_API}/generate",
            json=payload,
            headers=get_headers(),
            timeout=TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Response time: {elapsed_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            response_text = result.get('response', 'No response')
            done = result.get('done', False)
            
            print(f"✅ Native Generate Success!")
            print(f"📝 Response: {response_text[:200]}...")
            print(f"✅ Completed: {done}")
            
            # Print additional metrics if available
            if 'total_duration' in result:
                print(f"⏱️  Total duration: {result['total_duration'] / 1e9:.2f}s")
            if 'load_duration' in result:
                print(f"⏱️  Load duration: {result['load_duration'] / 1e9:.2f}s")
            if 'prompt_eval_count' in result:
                print(f"🔢 Prompt tokens: {result['prompt_eval_count']}")
            if 'eval_count' in result:
                completion_tokens = result['eval_count']
                print(f"🔢 Generated tokens: {completion_tokens}")
                # Calculate tokens per second
                if elapsed_time > 0:
                    tokens_per_sec = completion_tokens / elapsed_time
                    print(f"🚀 Tokens/second: {tokens_per_sec:.1f}")
                
            return True
        else:
            print(f"❌ Native Generate failed: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ Native Generate failed: {e}")
        return False

def test_openai_compatible_chat():
    """Test OpenAI compatible chat completion endpoint"""
    print(f"\n🧪 Testing OpenAI Compatible API - Chat Completion with model: {DEFAULT_MODEL}")
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful coding assistant."
            },
            {
                "role": "user", 
                "content": "Write a simple Python function to calculate the factorial of a number. Keep it concise."
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        print("⏳ Sending chat completion request...")
        start_time = time.time()
        
        response = requests.post(
            f"{OLLAMA_OPENAI_API}/chat/completions",
            json=payload,
            headers=get_headers(),
            timeout=TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Response time: {elapsed_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract response details
            choice = result.get('choices', [{}])[0]
            message = choice.get('message', {})
            content = message.get('content', 'No content')
            
            usage = result.get('usage', {})
            
            print(f"✅ OpenAI Compatible Chat Completion Success!")
            print(f"📝 Response: {content[:200]}...")
            print(f"🔢 Tokens - Prompt: {usage.get('prompt_tokens', 'N/A')}, "
                  f"Completion: {usage.get('completion_tokens', 'N/A')}, "
                  f"Total: {usage.get('total_tokens', 'N/A')}")
            
            # Calculate tokens per second
            completion_tokens = usage.get('completion_tokens', 0)
            if elapsed_time > 0 and completion_tokens:
                tokens_per_sec = completion_tokens / elapsed_time
                print(f"🚀 Tokens/second: {tokens_per_sec:.1f}")
            
            return True
        else:
            print(f"❌ OpenAI Compatible Chat Completion failed: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ OpenAI Compatible Chat Completion failed: {e}")
        return False

def test_streaming_chat():
    """Test streaming chat completion"""
    print(f"\n🌊 Testing OpenAI Compatible API - Streaming Chat with model: {DEFAULT_MODEL}")
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {
                "role": "user", 
                "content": "Count from 1 to 5 and explain each number briefly."
            }
        ],
        "max_tokens": 200,
        "temperature": 0.5,
        "stream": True
    }
    
    try:
        print("⏳ Starting streaming request...")
        
        streaming_headers = get_headers()
        streaming_headers["Accept"] = "text/event-stream"
        
        response = requests.post(
            f"{OLLAMA_OPENAI_API}/chat/completions",
            json=payload,
            headers=streaming_headers,
            timeout=TIMEOUT,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Streaming started!")
            print("📺 Stream content:")
            
            content_chunks = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            choice = data.get('choices', [{}])[0]
                            delta = choice.get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                print(content, end='', flush=True)
                                content_chunks.append(content)
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n✅ Streaming completed! Received {len(content_chunks)} chunks")
            return True
            
        else:
            print(f"❌ Streaming failed: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return False

def test_model_info():
    """Test getting specific model information"""
    print(f"\n📊 Testing Model Information for: {DEFAULT_MODEL}")
    
    try:
        # Try to get model info via native API
        response = requests.post(
            f"{OLLAMA_NATIVE_API}/show",
            json={"name": DEFAULT_MODEL},
            timeout=30,
            headers=get_headers()
        )
        
        if response.status_code == 200:
            model_info = response.json()
            print(f"✅ Model info endpoint working!")
            
            # Print relevant model information
            model_file = model_info.get('modelfile', 'N/A')
            parameters = model_info.get('parameters', 'N/A')
            template = model_info.get('template', 'N/A')
            
            print(f"📋 Model Details:")
            print(f"   - Parameters: {parameters}")
            print(f"   - Template length: {len(str(template)) if template != 'N/A' else 'N/A'} chars")
            print(f"   - Modelfile length: {len(str(model_file)) if model_file != 'N/A' else 'N/A'} chars")
            
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            print(f"📄 Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Model info failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Ollama API Service")
    print("=" * 60)
    print(f"🔗 Native API Base URL: {OLLAMA_NATIVE_API}")
    print(f"🔗 OpenAI Compatible API Base URL: {OLLAMA_OPENAI_API}")
    print(f"🤖 Default Model: {DEFAULT_MODEL}")
    print("=" * 60)
    
    # Test results tracking
    results = []
    
    # Test service health
    print("\n1️⃣ HEALTH CHECK")
    results.append(("Health Check", test_ollama_health()))
    
    # Only proceed if health check passes
    if not results[-1][1]:
        print("\n❌ Ollama service is not accessible!")
        print("💡 Make sure the ollama_api container is running:")
        print("💡 docker compose up -d ollama_api")
        return
    
    # Test native API
    print("\n2️⃣ NATIVE OLLAMA API TESTS")
    results.append(("Native - List Models", test_native_ollama_list_models()))
    results.append(("Native - Generate", test_native_ollama_generate()))
    results.append(("Native - Model Info", test_model_info()))
    
    # Test OpenAI compatible API
    print("\n3️⃣ OPENAI COMPATIBLE API TESTS")
    results.append(("OpenAI - List Models", test_openai_compatible_models()))
    results.append(("OpenAI - Chat Completion", test_openai_compatible_chat()))
    results.append(("OpenAI - Streaming Chat", test_streaming_chat()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print("=" * 60)
    print(f"🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Ollama service is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the service configuration.")
    
    print(f"🔗 Native API: {OLLAMA_NATIVE_API}")
    print(f"🔗 OpenAI Compatible API: {OLLAMA_OPENAI_API}")

if __name__ == "__main__":
    main()