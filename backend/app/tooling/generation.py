from typing import List, Generator
import requests
import json

MODEL_NAME = "gemma2:9b"
OLLAMA_BASE_URL = "http://localhost:11434"


def generate_text(prompt: str) -> str:
    """
    Generate text using Ollama API (non-streaming).
    
    Args:
        prompt: The input prompt for generation
        model: The model to use (defaults to gemma2:9b)
    
    Returns:
        The generated text response
    """
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )
    response.raise_for_status()
    return response.json()["response"]


def generate_text_stream(prompt: str) -> Generator[str, None, None]:
    """
    Generate text using Ollama API with streaming.
    
    Args:
        prompt: The input prompt for generation
        model: The model to use (defaults to gemma2:9b)
    
    Yields:
        Chunks of generated text as they arrive
    """
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            yield chunk["response"]
            if chunk.get("done"):
                break


def chat(messages: List[dict]) -> str:
    """
    Chat with the model using conversation history (non-streaming).
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: The model to use (defaults to gemma2:9b)
    
    Returns:
        The assistant's response
    """
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False
        }
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def chat_stream(messages: List[dict]) -> Generator[str, None, None]:
    """
    Chat with the model using conversation history (streaming).
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        model: The model to use (defaults to gemma2:9b)
    
    Yields:
        Chunks of the assistant's response as they arrive
    """
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True
        },
        stream=True
    )
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if "message" in chunk:
                yield chunk["message"]["content"]
            if chunk.get("done"):
                break


if __name__ == "__main__":
    # Example usage
    prompt = "Who was the guy who went down the mississippi river on a raft with a runaway slave?"
    # print("Non-streaming generation:")
    # print(generate_text(prompt))

    print("\nStreaming generation:")
    for text_chunk in generate_text_stream(prompt):
        print(text_chunk, end='', flush=True)

    # messages = [
    #     {"role": "user", "content": "Hello, who are you?"},
    #     {"role": "assistant", "content": "I am an AI created to assist you."},
    #     {"role": "user", "content": "Can you tell me a joke?"}
    # ]

    # print("\n\nNon-streaming chat:")
    # print(chat(messages))

    # print("\nStreaming chat:")
    # for chat_chunk in chat_stream(messages):
    #     print(chat_chunk, end='', flush=True)