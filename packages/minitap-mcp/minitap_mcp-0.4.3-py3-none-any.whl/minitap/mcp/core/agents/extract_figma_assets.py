"""Agent to extract Figma asset URLs from design context code."""

import re
import uuid
from pathlib import Path

from jinja2 import Template
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from minitap.mcp.core.llm import get_minitap_llm


class FigmaAsset(BaseModel):
    """Represents a single Figma asset."""

    variable_name: str = Field(description="The variable name from the code (e.g., imgSignal)")
    url: str = Field(description="The full URL to the asset")
    extension: str = Field(description="The file extension (e.g., svg, png, jpg)")


class ExtractedAssets(BaseModel):
    """Container for all extracted Figma assets."""

    assets: list[FigmaAsset] = Field(
        default_factory=list,
        description="List of all extracted assets from the Figma design context",
    )
    code_implementation: str = Field(
        description=(
            "The React/TypeScript code\n"
            "with the local url declarations turned into const declarations"
        )
    )


def sanitize_unicode_for_llm(text: str) -> str:
    """Remove or replace problematic Unicode characters that increase token consumption.

    Characters outside the Basic Multilingual Plane (BMP) like emoji and special symbols
    get escaped as \\U sequences when sent to LLMs, dramatically increasing token count
    and processing time.

    Args:
        text: The text to sanitize

    Returns:
        Text with problematic Unicode characters replaced with placeholders
    """

    # Replace characters outside BMP (U+10000 and above) with a placeholder
    # These are typically emoji, special symbols, or rare characters
    def replace_high_unicode(match):
        char = match.group(0)
        codepoint = ord(char)
        # Return a descriptive placeholder
        return f"[U+{codepoint:X}]"

    # Pattern matches characters with codepoints >= U+10000
    pattern = re.compile(r"[\U00010000-\U0010FFFF]")
    sanitized = pattern.sub(replace_high_unicode, text)

    return sanitized


async def extract_figma_assets(design_context_code: str) -> ExtractedAssets:
    """Extract asset URLs from Figma design context code.

    Args:
        design_context_code: The React/TypeScript code from get_design_context

    Returns:
        List of dictionaries containing variable_name, url, and extension
    """
    system_message = Template(
        Path(__file__).parent.joinpath("extract_figma_assets.md").read_text(encoding="utf-8")
    ).render()

    sanitized_code = sanitize_unicode_for_llm(design_context_code)

    messages: list[BaseMessage] = [
        SystemMessage(content=system_message),
        HumanMessage(
            content=f"Here is the code to analyze:\n\n```typescript\n{sanitized_code}\n```"
        ),
    ]

    llm = get_minitap_llm(
        model="openai/gpt-5",
        temperature=0,
        trace_id=str(uuid.uuid4()),
        remote_tracing=True,
    ).with_structured_output(ExtractedAssets)
    result: ExtractedAssets = await llm.ainvoke(messages)  # type: ignore

    return result
