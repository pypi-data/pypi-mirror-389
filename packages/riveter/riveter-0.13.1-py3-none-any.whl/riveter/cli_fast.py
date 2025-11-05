# type: ignore
"""Fast CLI entry point with transparent routing.

This module provides the main entry point for the Riveter CLI with integrated
fast path routing. It maintains complete backward compatibility while providing
performance optimizations for lightweight commands.

The entry point:
- Routes lightweight commands through fast path execution
- Delegates complex commands to the full CLI framework
- Preserves all existing behavior and output formatting
- Provides graceful fallback mechanisms
"""

import sys

from .fast_path import FastPathRouter


def main() -> None:
    """Main CLI entry point with fast path routing and graceful fallbacks.

    This function serves as the primary entry point for the Riveter CLI.
    It attempts to use fast path execution for lightweight commands and
    falls back to the full CLI framework for complex operations.

    Fallback strategy:
    1. Try fast path execution for lightweight commands
    2. Fall back to full CLI for complex commands or fast path failures
    3. Preserve all original error messages and exit codes
    4. Handle import errors and missing dependencies gracefully
    """
    # Get command line arguments (excluding program name)
    args = sys.argv[1:]

    # Try fast path execution first
    try:
        router = FastPathRouter()
        exit_code = router.route_command(args)

        if exit_code is not None:
            # Fast path successfully handled the command
            sys.exit(exit_code)

    except ImportError as e:
        # Fast path dependencies not available - fall back to full CLI
        _log_debug_fallback("fast_path_import_error", str(e))
    except Exception as e:
        # Unexpected error in fast path - fall back to full CLI
        _log_debug_fallback("fast_path_error", str(e))

    # Delegate to full CLI for complex commands or when fast path fails
    try:
        # Import the full CLI only when needed
        from .cli import main as cli_main

        cli_main()
    except ImportError as e:
        # Critical error - CLI module cannot be imported
        print(f"Critical error: Cannot import CLI module: {str(e)}", file=sys.stderr)
        print("Please check your Riveter installation.", file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        # Let SystemExit propagate normally (this is expected CLI behavior)
        raise
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def _log_debug_fallback(reason: str, message: str) -> None:
    """Log fallback reason for debugging purposes.

    Args:
        reason: Reason for fallback
        message: Error message
    """
    import os

    if os.getenv("RIVETER_DEBUG_FAST_PATH", "").lower() in ("1", "true", "yes"):
        print(f"Fast path fallback ({reason}): {message}", file=sys.stderr)


def create_transparent_entry_point() -> int:
    """Create a transparent entry point that preserves all CLI behavior.

    This function provides a drop-in replacement for the original CLI
    entry point while adding performance optimizations.

    Returns:
        Exit code from command execution
    """
    try:
        main()
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 0
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1


# For compatibility with existing entry point configuration
if __name__ == "__main__":
    main()
