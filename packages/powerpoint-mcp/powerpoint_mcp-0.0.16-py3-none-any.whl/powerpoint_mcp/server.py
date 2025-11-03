"""
PowerPoint MCP Server

A Model Context Protocol server for automating Microsoft PowerPoint using pywin32.
"""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from .tools.snapshot import powerpoint_snapshot
from .tools.presentation import manage_presentation
from .tools.switch_slide import powerpoint_switch_slide
from .tools.add_speaker_notes import powerpoint_add_speaker_notes
from .tools.list_templates import powerpoint_list_templates, generate_mcp_response
from .tools.analyze_template import powerpoint_analyze_template, generate_mcp_response as generate_analyze_response
from .tools.add_slide_with_layout import powerpoint_add_slide_with_layout, generate_mcp_response as generate_add_slide_response
from .tools.populate_placeholder import powerpoint_populate_placeholder, generate_mcp_response as generate_populate_response
from .tools.manage_slide import powerpoint_manage_slide, generate_mcp_response as generate_manage_slide_response
from .tools.evaluate import powerpoint_evaluate, generate_mcp_response as generate_evaluate_response

# Import tool descriptions
from . import tool_descriptions as desc

# Create the MCP server instance
mcp = FastMCP("PowerPoint MCP Server")


def tool_with_description(description: str):
    """Helper decorator that assigns docstring before @mcp.tool() processes it."""
    def decorator(func):
        func.__doc__ = description
        return mcp.tool()(func)
    return decorator


@tool_with_description(desc.MANAGE_PRESENTATION)
def manage_presentation_tool(
    action: str,
    file_path: Optional[str] = None,
    save_path: Optional[str] = None,
    template_path: Optional[str] = None,
    presentation_name: Optional[str] = None
) -> str:
    return manage_presentation(action, file_path, save_path, template_path, presentation_name)



@tool_with_description(desc.SLIDE_SNAPSHOT)
def slide_snapshot(slide_number: Optional[str] = None,
                  include_screenshot: Optional[bool] = True,
                  screenshot_filename: Optional[str] = None) -> str:
    # Convert string to int if provided
    if slide_number is not None:
        try:
            slide_number = int(slide_number)
        except ValueError:
            return f"Error: slide_number must be a valid integer, got '{slide_number}'"

    # Convert boolean if needed (handles JSON boolean type)
    if include_screenshot is None:
        include_screenshot = True

    result = powerpoint_snapshot(slide_number, include_screenshot, screenshot_filename)

    if "error" in result:
        return f"Error: {result['error']}"

    response_parts = [
        f"Slide context captured: {result['slide_number']} of {result['total_slides']}",
        f"Objects found: {result['object_count']}"
    ]

    # Add screenshot information if included
    if include_screenshot:
        if result.get('screenshot_saved'):
            response_parts.extend([
                "",
                f"Screenshot saved: {result['screenshot_path']}",
                f"Image size: {result['image_size']}",
                f"Objects annotated: {result['objects_annotated']} (green boxes with yellow ID labels)",
                f"{result['screenshot_message']}",
                "",
                "The screenshot file has been saved and can be viewed using the Read tool for visual reference."
            ])
        else:
            response_parts.extend([
                "",
                f"Screenshot failed: {result.get('screenshot_error', 'Unknown error')}"
            ])

    response_parts.extend(["", result['context']])

    return "\n".join(response_parts)


@tool_with_description(desc.SWITCH_SLIDE)
def switch_slide(slide_number: str) -> str:
    # Convert string to int
    try:
        slide_number = int(slide_number)
    except ValueError:
        return f"Error: slide_number must be a valid integer, got '{slide_number}'"

    result = powerpoint_switch_slide(slide_number)

    if "error" in result:
        return f"Error: {result['error']}"

    return f"Successfully switched to slide {result['slide_number']} of {result['total_slides']}"


@tool_with_description(desc.ADD_SPEAKER_NOTES)
def add_speaker_notes(slide_number: str, notes_text: str) -> str:
    # Convert string to int
    try:
        slide_number = int(slide_number)
    except ValueError:
        return f"Error: slide_number must be a valid integer, got '{slide_number}'"

    result = powerpoint_add_speaker_notes(slide_number, notes_text)

    if "error" in result:
        return f"Error: {result['error']}"

    return (f"Successfully added speaker notes to slide {result['slide_number']} of {result['total_slides']}\n"
            f"Notes length: {result['notes_length']} characters")


@tool_with_description(desc.LIST_TEMPLATES)
def list_templates() -> str:
    result = powerpoint_list_templates()
    return generate_mcp_response(result)


@tool_with_description(desc.ANALYZE_TEMPLATE)
def analyze_template(source: str = "current", detailed: bool = False) -> str:
    result = powerpoint_analyze_template(source)
    return generate_analyze_response(result, detailed)


@tool_with_description(desc.ADD_SLIDE_WITH_LAYOUT)
def add_slide_with_layout(template_name: str, layout_name: str, after_slide: int) -> str:
    result = powerpoint_add_slide_with_layout(template_name, layout_name, after_slide)
    return generate_add_slide_response(result)


@tool_with_description(desc.POPULATE_PLACEHOLDER)
def populate_placeholder(
    placeholder_name: str,
    content: str,
    content_type: str = "auto",
    slide_number: Optional[str] = None
) -> str:
    # Convert string to int if provided
    if slide_number is not None:
        try:
            slide_number = int(slide_number)
        except ValueError:
            return f"Error: slide_number must be a valid integer, got '{slide_number}'"

    result = powerpoint_populate_placeholder(placeholder_name, content, content_type, slide_number)
    return generate_populate_response(result)


@tool_with_description(desc.MANAGE_SLIDE)
def manage_slide(
    operation: str,
    slide_number: str,
    target_position: Optional[int] = None
) -> str:
    # Convert string to int
    try:
        slide_number = int(slide_number)
    except ValueError:
        return f"Error: slide_number must be a valid integer, got '{slide_number}'"

    result = powerpoint_manage_slide(operation, slide_number, target_position)
    return generate_manage_slide_response(result)


@tool_with_description(desc.POWERPOINT_EVALUATE)
def powerpoint_evaluate_tool(
    code: str,
    slide_number: Optional[str] = None,
    shape_ref: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    # Convert string to int if provided
    if slide_number is not None:
        try:
            slide_number = int(slide_number)
        except ValueError:
            return f"Error: slide_number must be a valid integer, got '{slide_number}'"

    result = powerpoint_evaluate(code, slide_number, shape_ref, description)
    return generate_evaluate_response(result)


def main():
    """Main entry point for the PowerPoint MCP server."""
    mcp.run()