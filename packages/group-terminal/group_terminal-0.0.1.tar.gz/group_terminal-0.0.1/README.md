# Introduction

`group-terminal` is a minimalistic, terminal-based group chat system designed for testing and prototyping AI service integrations. Most group chat systems require authentication, databases, and user management before you can test a single message handler or prototype collaboration of user groups with AI. `group-terminal` eliminates this complexity by providing a minimal WebSocket-based chat server and [Rich](https://github.com/Textualize/rich)-powered terminal clients that let you focus on testing your integration logic rather than infrastructure setup.

The project delivers four capabilities to accelerate development workflows. A zero-configuration design means no authentication or database setup is required. Server-side message handlers let you build and test services that respond to group chat messages. The Rich-based terminal interface provides immediate visual feedback with configurable colors for different message types. Finally, the explicit testing-focused design ensures you spend time building features rather than maintaining production concerns like security or persistence.

> [!NOTE]
> `group-terminal` uses [termios](https://docs.python.org/3/library/termios.html) for terminal control and is Unix-specific. It will not work on Windows systems.

## Documentation

- [User Guide](https://gradion-ai.github.io/group-terminal/): Overview and getting started guide
- [API Documentation](https://gradion-ai.github.io/group-terminal/api/server/): Complete API reference

## LLM-Readable Documentation

For AI assistants and LLM-based tools, optimized documentation formats are available:

- [llms.txt](https://gradion-ai.github.io/group-terminal/llms.txt): Concise documentation suitable for LLM context windows
- [llms-full.txt](https://gradion-ai.github.io/group-terminal/llms-full.txt): Complete documentation with full API details

## Development

For development setup, see [DEVELOPMENT.md](DEVELOPMENT.md)
