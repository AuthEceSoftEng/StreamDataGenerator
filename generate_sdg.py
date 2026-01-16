#!/usr/bin/env python3
"""
SDG File Generator
==================

Generates an SDG file for StreamDataGenerator using a text description.
The SDG file is stored by default in the same path as the text description.

An example is shown in examples_nl_descriptions/onlineretail.txt
The SDG file can then be used to create the dataset generator.

To create a good SDG file, we produce here a prompt that guides the LLM to produce
a good quality SDG file. The prompt template is stored in the file prompt_template.txt
The prompt template uses placeholders {description} and {examples} to be replaced
with the actual text description and with some examples of SDG files such as the ones
stored in the folder examples (ending in .sdg).

Note that this code requires an API token for authentication, as it uses an external LLM.
API Connection details available at file modelapi.py

Usage:
    python generate_sdg.py <input_description_file> [-o <output_sdg_file>]
    
    # Or using environment variables:
    # LLM_PROVIDER=openai LLM_API_KEY=sk-... python generate_sdg.py description.txt
    
Examples:
    python generate_sdg.py examples_nl_descriptions/onlineretail.txt
    python generate_sdg.py description.txt -o my_generator.sdg
"""

import os
import re
import sys
import argparse
from pathlib import Path

from modelapi import create_provider, create_provider_from_env


# Default paths relative to this script
SCRIPT_DIR = Path(__file__).parent
EXAMPLES_DIR = SCRIPT_DIR / "examples"
PROMPT_TEMPLATE_FILE = SCRIPT_DIR / "prompt_template.txt"


def load_prompt_template(template_path):
    """
    Load the prompt template from file.
    
    Args:
        template_path: Optional path to template file. Uses default if not provided.
        
    Returns:
        The prompt template string with {description} and {examples} placeholders.
    """
    path = template_path or PROMPT_TEMPLATE_FILE
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def load_examples(examples_dir, max_examples = 3):
    """
    Load example SDG files to include in the prompt.
    
    Args:
        examples_dir: Directory containing .sdg example files
        max_examples: Maximum number of examples to include
        
    Returns:
        Formatted string containing the examples
    """
    path = examples_dir or EXAMPLES_DIR
    if not path.exists():
        print(f"Warning: Examples directory not found: {path}")
        return ""
    
    # Get all .sdg files
    sdg_files = list(path.glob("*.sdg"))
    
    if not sdg_files:
        print(f"Warning: No .sdg files found in {path}")
        return ""
    
    # Select a diverse set of examples (loan, friedman, stagger are good choices)
    preferred_files = ['loandatadescriptor.sdg', 'friedmandriftdescriptor.sdg', 
                       'staggerdatadescriptor.sdg', 'mixeddatadescriptor.sdg']
    
    selected = []
    for preferred in preferred_files:
        matching = [f for f in sdg_files if f.name == preferred]
        if matching and len(selected) < max_examples:
            selected.append(matching[0])
    
    # Fill remaining slots with other files
    for f in sdg_files:
        if f not in selected and len(selected) < max_examples:
            selected.append(f)
    
    # Format examples
    examples_text = []
    for sdg_file in selected:
        with open(sdg_file, 'r', encoding='utf-8') as f:
            content = f.read()
        examples_text.append(f"### Example: {sdg_file.name}\n```\n{content}\n```")
    
    return "\n\n".join(examples_text)


def build_prompt(description, examples, template):
    """
    Build the final prompt by replacing placeholders in the template.
    
    Args:
        description: The natural language description of the desired generator
        examples: Formatted example SDG files
        template: The prompt template
        
    Returns:
        The complete prompt ready to send to the LLM
    """
    return template.replace("{description}", description).replace("{examples}", examples)


def extract_sdg_from_response(response):
    """
    Extract the SDG content from the LLM response.
    
    The response may contain the SDG within code blocks or as plain text.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned SDG content
    """
    # Try to extract from code block first (```sdg or ``` or ```text)
    code_block_pattern = r'```(?:sdg|text|)?\s*\n(.*?)\n```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        # Return the largest match (likely the full SDG)
        return max(matches, key=len).strip()
    
    # If no code block, look for dataset ... end_dataset pattern
    dataset_pattern = r'(dataset\s+\w+.*?end_dataset)'
    matches = re.findall(dataset_pattern, response, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Return original response if no patterns found
    return response.strip()


def generate_sdg(description, provider, template_path = None, examples_dir = None, max_examples = 3, temperature = 0.3, max_tokens = 4096):
    """
    Generate an SDG file from a natural language description.
    
    Args:
        description: Natural language description of the desired data stream
        provider: LLM provider instance
        template_path: Optional custom prompt template path
        examples_dir: Optional custom examples directory
        max_examples: Number of examples to include in prompt
        temperature: LLM temperature (lower = more deterministic)
        max_tokens: Maximum response tokens
        
    Returns:
        Generated SDG file content
    """
    # Load template and examples
    template = load_prompt_template(template_path)
    examples = load_examples(examples_dir, max_examples)
    
    # Build the prompt
    prompt = build_prompt(description, examples, template)
    
    # Call the LLM
    print("Generating SDG file...")
    response = provider.chat(
        message=prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # Extract and return SDG content
    return extract_sdg_from_response(response)


def generate_sdg_from_file(input_file, output_file = None, provider = None, **kwargs):
    """
    Generate an SDG file from a description file.
    
    Args:
        input_file: Path to text file containing the description
        output_file: Optional output path. Defaults to same directory as input with .sdg extension
        provider: Optional LLM provider. Creates from env if not provided
        **kwargs: Additional arguments passed to generate_sdg()
        
    Returns:
        Path to the generated SDG file
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read description
    with open(input_path, 'r', encoding='utf-8') as f:
        description = f.read().strip()
    
    if not description:
        raise ValueError(f"Input file is empty: {input_path}")
    
    # Determine output path
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = input_path.with_suffix('.sdg')
    
    # Create provider if not provided
    if provider is None:
        provider = create_provider_from_env()
    
    # Generate SDG
    sdg_content = generate_sdg(description, provider, **kwargs)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sdg_content)
    
    print(f"Generated SDG file: {output_path}")
    return output_path


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Generate SDG files from natural language descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_sdg.py description.txt
  python generate_sdg.py description.txt -o output.sdg
  python generate_sdg.py description.txt --provider openai --model gpt-4
  python generate_sdg.py description.txt --provider ollama --model llama3
  
Environment Variables:
  LLM_PROVIDER      Provider type: 'openai', 'ollama', 'custom'
  LLM_API_KEY       API key for authentication
  LLM_BASE_URL      Base URL for the API
  LLM_MODEL         Model name/ID
  LLM_PROVIDER_NAME Provider name for custom API (e.g., 'gcp')
        """
    )
    
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to text file containing natural language description"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output SDG file path (default: same as input with .sdg extension)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=['openai', 'ollama', 'custom'],
        default=None,
        help="LLM provider type (overrides LLM_PROVIDER env var)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name/ID (overrides LLM_MODEL env var)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (overrides LLM_API_KEY env var)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API base URL (overrides LLM_BASE_URL env var)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="LLM temperature (default: 0.3)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum response tokens (default: 4096)"
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=3,
        help="Number of examples to include in prompt (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Build provider kwargs from CLI arguments
    provider_kwargs = {}
    if args.api_key:
        provider_kwargs['api_key'] = args.api_key
    if args.base_url:
        provider_kwargs['base_url'] = args.base_url
    if args.model:
        provider_kwargs['model'] = args.model
    
    # Create provider
    if args.provider:
        provider = create_provider(args.provider, **provider_kwargs)
    elif provider_kwargs:
        # If any provider kwargs specified but no provider type, use env
        config = {
            'provider_type': os.environ.get('LLM_PROVIDER', 'openai'),
            **provider_kwargs
        }
        provider = create_provider(config.pop('provider_type'), **config)
    else:
        provider = create_provider_from_env()
    
    try:
        output_path = generate_sdg_from_file(
            input_file=args.input_file,
            output_file=args.output,
            provider=provider,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            max_examples=args.max_examples
        )
        print(f"Success! SDG file written to: {output_path}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error generating SDG: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())