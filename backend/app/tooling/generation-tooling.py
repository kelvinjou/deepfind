# Tooling for generative tasks within the application

from typing import List, Generator

from generation import generate_text

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

def prompt_refinement(original_prompt: str) -> str:
    list_of_tools = [
        "[File Operations] move_files_to_directory(file_paths, target_directory): Move files to a specified directory, creating it if needed",
        "[File Operations] rename_files(file_paths, new_names): Rename multiple files with new names",
        "[File Operations] delete_files(file_paths): Delete specified files (requires confirmation)",
        "[File Operations] make_copy_of_files(file_paths, target_directory): Copy files to a target directory",
        "[File Operations] make_copy_of_directory(source_directory, target_directory): Copy an entire directory",
        "[Conversion] convert_file_types(file_paths, target_extension): Convert files from one format to another",
        "[Tagging (macOS)] tag_files(file_paths, tag, color): Tag files with macOS Finder tags (colors 0-7)",
        "[Tagging (macOS)] get_files_with_tag(directory, tag): Get all files with a specific tag in a directory",
        "[Search] search_files_by_pattern(directory, pattern): Search for files matching a name pattern",
        "[Search] search_files_by_tags(directory, tag_key, tag_value): Search files by metadata tags",
        "[Filtering] filter_files_by_date(directory, start_date, end_date): Filter files by modification date range",
        "[Filtering] filter_files_by_size(directory, min_size, max_size): Filter files by size range (bytes)",
        "[Filtering] filter_files_by_type(directory, file_extension): Filter files by extension",
        "[Recent Files] get_most_recently_modified_files(directory, n): Get the n most recently modified files",
    ]
    
    prompt = (
        f"Refine the following prompt given that it will be passed to an MCP with multiple tooling calls from the following list: {', '.join(list_of_tools)}.\n\n"
        f"ONLY return the refined prompt without any additional explanation or text.\n\n"
        f"Original Prompt: {original_prompt}\n\n"
    )
    return generate_text(prompt)


if __name__ == "__main__":
    sample_text = "Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior. It encompasses a variety of techniques and approaches, including machine learning, natural language processing, and robotics. AI has the potential to revolutionize many industries by automating tasks, improving decision-making, and enhancing user experiences."
    print("Summary:")
    print(summarize_text(sample_text))
    
    print("\nGenerated File Name:")
    print(generate_file_name(sample_text, max_length=5, include_date=True, include_topic=True))
    
    print("\nRefined Prompt:")
    original_prompt = "I need to organize my files on AI, travel, and finances better."
    print(prompt_refinement(original_prompt))