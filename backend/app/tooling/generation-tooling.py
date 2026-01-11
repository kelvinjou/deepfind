# Tooling for generative tasks within the application

from typing import List, Generator

from backend.app.tooling.generation import generate_text

def summarize_text(text: str) -> str:
    return generate_text(f"Summarize the following text:\n\n{text}")

def generate_file_name(
    content: str,
    max_length: int = 10,
    include_date: bool = False,
    include_topic: bool = False
) -> str:
    prompt = f"Generate a title for the following content"
    if include_date:
        prompt += " that includes the date"
    if include_topic:
        prompt += " that reflects the main topic"
    prompt += f". The title should be no longer than {max_length} words.\n"
    prompt += f"\nContent:\n{content}"
    return generate_text(prompt)

def prompt_refinement(original_prompt: str, context: str) -> str:
    prompt = (
        f"Refine the following prompt based on the given context.\n\n"
        f"Original Prompt: {original_prompt}\n\n"
        f"Context: {context}\n\n"
    )
    return generate_text(prompt)
