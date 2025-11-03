"""Agent to extract Figma asset URLs from design context code."""

from pathlib import Path
from uuid import uuid4

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

    messages: list[BaseMessage] = [
        SystemMessage(content=system_message),
        HumanMessage(
            content=f"Here is the code to analyze:\n\n```typescript\n{design_context_code}\n```"
        ),
    ]

    llm = get_minitap_llm(
        trace_id=str(uuid4()),
        remote_tracing=True,
        model="google/gemini-2.5-pro",
        temperature=0,
    ).with_structured_output(ExtractedAssets)

    result: ExtractedAssets = await llm.ainvoke(messages)  # type: ignore

    return result
