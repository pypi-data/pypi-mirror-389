# Agentlys Tools

Repository of tools for [agentlys](https://github.com/myriade-ai/agentlys).

## Installation

Install with all tools:

```bash
pip install 'agentlys-tools[all]'
```

Install with only specific tools:

```bash
pip install 'agentlys-tools[code-editor,terminal]'
```

## Available Tools

- Terminal: Open a shell session, run commands and scripts
- CodeEditor: Code editor for working on code files

## Usage

```python
from agentlys import Agentlys
from agentlys_tools.code_editor import CodeEditor
from agentlys_tools.terminal import Terminal

agent = Agentlys()
code_editor = CodeEditor()
agent.add_tool(code_editor, "code_editor")
agent.add_tool(Terminal)

instruction = """
You are a developer agent.
Create a new file called 'test.py' and write 'print('Hello, World!')' to it.
"""

for msg in agent.run_conversation(instruction):
    print(msg.content.to_terminal())
```
