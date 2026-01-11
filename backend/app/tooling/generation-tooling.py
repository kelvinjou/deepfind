# Tooling for generative tasks within the application

from typing import Dict, List, Generator

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


def refined_vector_query(prompt: str): # might simplify too much?
    prompt = (
        f"Refine the following prompt to be more suitable for one or multiple mcp calls for a vector database query. "
        f"Focus on key concepts and important terms.\n\n"
        f"Make sure the query specifically splits concepts into separate terms for better vector matching.\n\n"
        f"List the key topics/concepts using commas + new lines to separate them.\n\n"
        f"ONLY return the refined query without any additional explanation or text.\n\n"
        f"Include a header line that says: 'Search Query for the following topics:' before the refined query.\n\n"
        f"Original Prompt: {prompt}\n\n"
    )
    return generate_text(prompt)

def generate_outline(text, num_points: int = 5) -> str:
    prompt = (
        f"Generate an outline with {num_points} main points for the following text:\n\n{text}\n\n"
        f"Format the outline as a numbered list."
    )
    return generate_text(prompt)

# Synthesize multiple pieces of information into a coherent summary and sites the documents used
def synthesize_information(document_text: List[tuple]) -> str:  # list of (document_name, document_content) tuples
    combined_text = "\n\n".join([f"Document: {name}\nContent: {content}" for name, content in document_text])
    prompt = (
        f"Synthesize the following documents into a coherent summary. "
        f"Cite the documents used in the synthesis by their name.\n\n"
        f"{combined_text}\n\n"
        f"Provide a clear and concise summary."
    )
    return generate_text(prompt)


def compare_files(file_path_1: str, file_path_2: str) -> str:
    with open(file_path_1, 'r') as file1, open(file_path_2, 'r') as file2:
        content1 = file1.read()
        content2 = file2.read()
    
    prompt = (
        f"Compare the following two files and highlight their differences:\n\n"
        f"File 1 Content:\n{content1}\n\n"
        f"File 2 Content:\n{content2}\n\n"
        f"Provide a summary of the differences."
    )
    return generate_text(prompt)


def generate_study_guide(text: str, num_questions: int = 5) -> str:
    prompt = (
        f"Generate a study guide based on the following text. "
        f"Include {num_questions} questions that cover the key concepts:\n\n{text}\n\n"
        f"Format the study guide with questions numbered."
    )
    return generate_text(prompt)



if __name__ == "__main__":
    # sample_text = "Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior. It encompasses a variety of techniques and approaches, including machine learning, natural language processing, and robotics. AI has the potential to revolutionize many industries by automating tasks, improving decision-making, and enhancing user experiences."
    # print("Summary:")
    # print(summarize_text(sample_text))
    
    # print("\nGenerated File Name:")
    # print(generate_file_name(sample_text, max_length=5, include_date=True, include_topic=True))
    
    # print("\nRefined Prompt:")
    # original_prompt = "I need to organize my files on AI, travel, and finances better."
    # print(prompt_refinement(original_prompt))
    
    # print("\nRefined Vector Query:")
    # query_prompt = "Find documents related to advancements in artificial intelligence, machine learning, my taxes, and my travel documents."
    # print(refined_vector_query(query_prompt))
    
    print("\nGenerated Outline:")
    sample_text = "Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior. It encompasses a variety of techniques and approaches, including machine learning, natural language processing, and robotics. AI has the potential to revolutionize many industries by automating tasks, improving decision-making, and enhancing user experiences."
    print(generate_outline(sample_text, num_points=4))
    
    print("\nSynthesize Information:")
    documents = (
        ("AI_Overview.txt", "Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior."),
        ("AI_Applications.txt", "AI has applications in various fields including healthcare, finance, and transportation."),
    )
    print(synthesize_information(documents))