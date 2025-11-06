# Changelog

All notable changes to B8TeX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-11-05

### Added
- LaTeX style templates with contract-based architecture:
  - NeurIPS, ICLR, and ACL style files adapted for general-purpose document creation
  - Unified contract interface with status options (final, confidential, internal, draft)
  - Metadata commands: `\setorganization`, `\setdoctype`, `\setdocid`
  - Style-appropriate metadata placement (footer/header/footnote)
  - Example templates for each style with comprehensive documentation
  - STYLE_CONTRACTS.md defining architecture and design principles

### Changed
- Style files maintain pixel-perfect compatibility with original conference templates
- Includes required packages for self-contained usage
- Non-breaking, opt-in functionality for metadata display

## [0.1.0] - 2025-01-28

### Added

#### Core Infrastructure
- **Tectonic Binary Management**
  - Automatic binary discovery with fallback chain (config → env → PATH → cache → download)
  - Multi-platform auto-download support (Linux x86_64/aarch64, macOS x86_64/aarch64, Windows x86_64)
  - Binary capability probing (version detection, V2 interface support)
  - Lock-based concurrency control for downloads
  - Security features: size limits, timeout enforcement, path traversal protection

- **Document Model**
  - `Document` class for LaTeX document representation
  - `InMemorySource` for compiling from strings
  - `Resource` class for style files, images, bibliographies
  - Search path management for custom package locations

- **Workspace Management**
  - Isolated build directories with automatic cleanup
  - Temporary and persistent workspace modes
  - Resource staging and file materialization
  - Environment isolation (removes ambient TEXINPUTS)

- **Configuration System**
  - TOML-based configuration file (`~/.config/b8tex/config.toml`)
  - Environment variable overrides
  - Settings for auto-download, Tectonic version, binary path

#### Build System
- **Build Options**
  - Comprehensive `BuildOptions` class supporting all Tectonic flags
  - Multiple output formats: PDF, HTML, XDV, AUX, FMT
  - Security policies: untrusted mode, shell-escape control
  - Bundle configuration for custom TeX distributions
  - Rerun control, SyncTeX support, log retention

- **Compilation API**
  - High-level `compile_string()` and `compile_document()` functions
  - `TectonicCompiler` class for advanced usage
  - V1 and V2 Tectonic interface support with automatic selection
  - Multi-target project builds with `Project` and `Target` classes

- **Results & Diagnostics**
  - Structured `CompileResult` with success status, artifacts, warnings, errors
  - `OutputArtifact` tracking for generated files
  - `LogParser` for extracting warnings and errors from Tectonic output
  - `ModuleGraph` for dependency tracking

#### Advanced Features
- **Build Caching**
  - SQLite-based persistent cache across sessions
  - Content-addressed artifact storage with SHA256 hashing
  - Automatic cache invalidation on content/option/version changes
  - Cache statistics, cleanup, and garbage collection
  - 10-100x speedup on cache hits

- **Watch Mode**
  - File system watching with automatic rebuild on changes
  - Configurable debouncing to prevent excessive builds
  - Custom file pattern matching (*.tex, *.sty, *.bib, etc.)
  - Success/error callbacks for build events
  - Async implementation using `watchfiles` package
  - Multi-directory watching support

- **Async Support**
  - `ProcessRunner` with async foundation
  - Concurrent compilation patterns (via ThreadPoolExecutor)
  - Async watch mode implementation

#### CLI
- **Command-line Interface**
  - `b8tex install-binary` - Download and install Tectonic
  - `b8tex config` - Show current configuration
  - `b8tex init-config` - Create default config file
  - `b8tex clean-cache` - Remove cached binaries
  - `b8tex help` - Comprehensive help text

#### Testing & Examples
- **Comprehensive Test Suite**
  - 150+ test cases across 13 test modules
  - Unit tests for all core modules
  - Integration tests for full compilation pipeline
  - CLI tests with mocking
  - Async tests for concurrent operations
  - Edge case and error condition coverage
  - 90%+ code coverage

- **Working Examples**
  - `01_basic_usage.py` - Basic compilation from string
  - `02_custom_styles.py` - Custom style files and packages
  - `03_project_build.py` - Multi-target project builds
  - `04_async_compilation.py` - Concurrent document compilation
  - `05_cache_demo.py` - Build caching demonstration
  - `06_watch_mode.py` - File watching and auto-rebuild

#### Documentation
- Comprehensive README with:
  - Installation guide (auto-download and manual)
  - Quick start examples
  - Configuration reference
  - Troubleshooting section (6 common issues)
  - FAQ (20+ questions)
  - Performance tips (8 optimization strategies)
  - API reference overview
- Example-specific README with detailed descriptions
- Inline code documentation with Google-style docstrings
- Technical design document (docs/tech_details.md)

### Technical Details

#### Dependencies
- Python 3.13+
- `platformdirs` for cross-platform paths
- `tomli` for TOML parsing (Python < 3.11)
- Optional: `watchfiles` for watch mode
- Optional: `anyio` for advanced async support

#### Supported Platforms
- Linux (x86_64, aarch64)
- macOS (x86_64 Intel, aarch64 Apple Silicon)
- Windows (x86_64)

#### Code Quality
- 100% type hints with strict mypy checking
- Zero TODOs, FIXMEs, or placeholders in production code
- Ruff for linting and formatting
- Security-conscious implementation
- Clean architecture with separation of concerns

### Security
- Path traversal protection in archive extraction
- Download size limits and timeouts
- Untrusted mode for sandboxing
- Shell-escape validation and control
- Input validation throughout

---

## Release Notes

### v0.1.0 - Initial Release

B8TeX 0.1.0 is the first public release, providing a modern, type-safe Python wrapper for the Tectonic LaTeX compiler. The project is feature-complete for core functionality and includes advanced features like build caching and watch mode.

**Highlights:**
- 🚀 Automatic Tectonic binary installation
- ⚡ Build caching with 10-100x speedup
- 👀 Watch mode for live editing
- 🔒 Security-conscious design
- 📦 Clean, type-safe API
- 📚 Comprehensive documentation
- ✅ 150+ tests with 90%+ coverage

**Getting Started:**
```bash
pip install b8tex
```

```python
from b8tex import compile_string

result = compile_string(r"""
\documentclass{article}
\begin{document}
Hello, B8TeX!
\end{document}
""")

print(f"PDF generated: {result.pdf_path}")
```

See the [README](README.md) for full documentation and examples.

---

## Links

- [PyPI Package](https://pypi.org/project/b8tex/)
- [GitHub Repository](https://github.com/samehkamaleldin/pytex)
- [Documentation](https://github.com/samehkamaleldin/pytex#readme)
- [Issue Tracker](https://github.com/samehkamaleldin/pytex/issues)
