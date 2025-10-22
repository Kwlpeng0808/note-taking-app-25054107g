"""Top-level package marker for the project's source modules.

Creating this file allows absolute imports like `from src.translation_worker import ...`
to be resolved by tools like Pylance and at runtime when the workspace root is on
the Python path.
"""

# Export common submodules for convenience (optional)
__all__ = [
    'llm',
    'main',
    'models',
    'routes',
    'translation_worker',
]
