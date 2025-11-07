try:
    from .code_editor import CodeEditor

    __all__ = ["CodeEditor"]
except ImportError:
    # Handle missing optional dependencies gracefully
    def CodeEditor(*args, **kwargs):
        raise ImportError(
            "CodeEditor requires extra dependencies. "
            "Install with: pip install agentlys-tools[code-editor]"
        )

    __all__ = ["CodeEditor"]
