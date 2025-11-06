# type: ignore
"""Modernized fast CLI entry point with advanced performance optimizations.

This module provides the main entry point for the Riveter CLI with integrated
fast path routing and advanced performance optimizations. It maintains complete
backward compatibility while providing significant startup time improvements.

Key performance optimizations:
- Lazy loading of all heavy dependencies
- Intelligent command routing with minimal overhead
- Startup time profiling and monitoring
- Memory-efficient import management
- Graceful fallback mechanisms with error preservation
"""

import os
import sys
import time
from typing import Any, Callable, List, Optional

from .cli.performance import (
    StartupProfiler,
    get_fast_path_optimizer,
    setup_cli_performance_optimizations,
)
from .fast_path import FastPathRouter


def main() -> None:
    """Main entry point with performance optimizations."""
    # Set up performance optimizations
    profiler, optimizer = setup_cli_performance_optimizations()
    profiler.checkpoint("performance_setup_complete")

    # Try fast path first
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:]

        fast_result = optimizer.try_fast_path(command, args)
        if fast_result is not None:
            print(fast_result)
            profiler.checkpoint("fast_path_executed")
            return

    profiler.checkpoint("fast_path_check_complete")

    # Fall back to full CLI
    try:
        from .main import main as full_main

        profiler.checkpoint("full_cli_imported")
        full_main()
        profiler.checkpoint("full_cli_executed")
    except Exception as e:
        # Graceful fallback with error preservation
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


class PerformanceMonitor:
    """Monitor and profile CLI startup performance."""

    def __init__(self) -> None:
        """Initialize performance monitor."""
        self._start_time = time.perf_counter()
        self._checkpoints: list[tuple[str, float]] = []
        self._enabled = os.getenv("RIVETER_PROFILE_STARTUP", "").lower() in ("1", "true", "yes")

    def checkpoint(self, name: str) -> None:
        """Record a performance checkpoint.

        Args:
            name: Checkpoint name
        """
        if self._enabled:
            elapsed = time.perf_counter() - self._start_time
            self._checkpoints.append((name, elapsed))

    def report(self) -> None:
        """Report performance metrics if enabled."""
        if not self._enabled or not self._checkpoints:
            return

        total_time = time.perf_counter() - self._start_time
        print(f"\n[STARTUP PROFILE] Total time: {total_time:.3f}s", file=sys.stderr)

        for name, elapsed in self._checkpoints:
            print(f"[STARTUP PROFILE] {name}: {elapsed:.3f}s", file=sys.stderr)


class LazyImportManager:
    """Manage lazy imports with performance optimization."""

    def __init__(self) -> None:
        """Initialize lazy import manager."""
        self._import_cache: dict[str, Any] = {}
        self._import_times: dict[str, float] = {}

    def lazy_import(self, module_name: str, attr_name: str | None = None) -> Any:
        """Lazy import with caching and performance tracking.

        Args:
            module_name: Module to import
            attr_name: Attribute to get from module

        Returns:
            Imported module or attribute
        """
        cache_key = f"{module_name}.{attr_name}" if attr_name else module_name

        if cache_key in self._import_cache:
            return self._import_cache[cache_key]

        start_time = time.perf_counter()

        try:
            module = __import__(module_name, fromlist=[attr_name] if attr_name else [])
            result = getattr(module, attr_name) if attr_name else module

            self._import_cache[cache_key] = result
            self._import_times[cache_key] = time.perf_counter() - start_time

            return result

        except ImportError as e:
            # Log import failure for debugging
            if os.getenv("RIVETER_DEBUG_IMPORTS", "").lower() in ("1", "true", "yes"):
                print(f"Import failed: {cache_key} - {e}", file=sys.stderr)
            raise

    def get_import_stats(self) -> dict[str, float]:
        """Get import timing statistics.

        Returns:
            Dictionary of import names to timing
        """
        return self._import_times.copy()


# Global instances for performance monitoring
_perf_monitor = PerformanceMonitor()
_import_manager = LazyImportManager()


def main() -> None:
    """Main CLI entry point with advanced performance optimizations.

    This function serves as the primary entry point for the Riveter CLI.
    It uses advanced performance optimizations including:
    - Startup time profiling
    - Lazy loading of all dependencies
    - Intelligent command routing
    - Memory-efficient execution paths
    """
    _perf_monitor.checkpoint("entry_point")

    # Get command line arguments (excluding program name)
    args = sys.argv[1:]

    _perf_monitor.checkpoint("args_parsed")

    # Try fast path execution first with performance monitoring
    try:
        router = FastPathRouter()
        _perf_monitor.checkpoint("fast_path_router_created")

        exit_code = router.route_command(args)
        _perf_monitor.checkpoint("fast_path_routing_complete")

        if exit_code is not None:
            # Fast path successfully handled the command
            _perf_monitor.checkpoint("fast_path_success")
            _perf_monitor.report()
            sys.exit(exit_code)

    except ImportError as e:
        # Fast path dependencies not available - fall back to full CLI
        _log_debug_fallback("fast_path_import_error", str(e))
        _perf_monitor.checkpoint("fast_path_import_error")
    except Exception as e:
        # Unexpected error in fast path - fall back to full CLI
        _log_debug_fallback("fast_path_error", str(e))
        _perf_monitor.checkpoint("fast_path_error")

    # Delegate to full CLI for complex commands or when fast path fails
    _perf_monitor.checkpoint("delegating_to_full_cli")

    try:
        # Use lazy import for the full CLI to minimize startup overhead
        cli_main = _import_manager.lazy_import("riveter.cli", "main")
        _perf_monitor.checkpoint("full_cli_imported")

        cli_main()
        _perf_monitor.checkpoint("full_cli_complete")

    except ImportError as e:
        # Critical error - CLI module cannot be imported
        print(f"Critical error: Cannot import CLI module: {e!s}", file=sys.stderr)
        print("Please check your Riveter installation.", file=sys.stderr)
        _perf_monitor.checkpoint("critical_import_error")
        _perf_monitor.report()
        sys.exit(1)
    except SystemExit:
        # Let SystemExit propagate normally (this is expected CLI behavior)
        _perf_monitor.checkpoint("system_exit")
        _perf_monitor.report()
        raise
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nOperation cancelled by user", file=sys.stderr)
        _perf_monitor.checkpoint("keyboard_interrupt")
        _perf_monitor.report()
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected error: {e!s}", file=sys.stderr)
        _perf_monitor.checkpoint("unexpected_error")
        _perf_monitor.report()
        sys.exit(1)

    _perf_monitor.report()


def _log_debug_fallback(reason: str, message: str) -> None:
    """Log fallback reason for debugging purposes with performance context.

    Args:
        reason: Reason for fallback
        message: Error message
    """
    if os.getenv("RIVETER_DEBUG_FAST_PATH", "").lower() in ("1", "true", "yes"):
        elapsed = time.perf_counter() - _perf_monitor._start_time
        print(f"Fast path fallback at {elapsed:.3f}s ({reason}): {message}", file=sys.stderr)


def create_transparent_entry_point() -> int:
    """Create a transparent entry point with performance optimization.

    This function provides a drop-in replacement for the original CLI
    entry point while adding advanced performance optimizations.

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
        print(f"Unexpected error: {e!s}", file=sys.stderr)
        return 1


def create_optimized_command_wrapper(command_func: Callable[..., Any]) -> Callable[..., Any]:
    """Create an optimized wrapper for CLI commands with lazy loading.

    Args:
        command_func: Command function to wrap

    Returns:
        Optimized command wrapper
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Optimized command wrapper with lazy loading."""
        start_time = time.perf_counter()

        try:
            result = command_func(*args, **kwargs)

            # Log performance if enabled
            if os.getenv("RIVETER_PROFILE_COMMANDS", "").lower() in ("1", "true", "yes"):
                elapsed = time.perf_counter() - start_time
                print(f"[COMMAND PROFILE] {command_func.__name__}: {elapsed:.3f}s", file=sys.stderr)

            return result

        except Exception as e:
            # Log error with timing context
            if os.getenv("RIVETER_DEBUG_COMMANDS", "").lower() in ("1", "true", "yes"):
                elapsed = time.perf_counter() - start_time
                print(
                    f"[COMMAND ERROR] {command_func.__name__} failed at {elapsed:.3f}s: {e}",
                    file=sys.stderr,
                )
            raise

    return wrapper


def optimize_startup_imports() -> None:
    """Pre-optimize common imports for faster startup."""
    if os.getenv("RIVETER_PRELOAD_IMPORTS", "").lower() in ("1", "true", "yes"):
        # Pre-load commonly used modules in background
        try:
            _import_manager.lazy_import("riveter.version", "get_version")
            _import_manager.lazy_import("riveter.lazy_imports", "lazy_importer")
        except ImportError:
            # Ignore import errors during pre-loading
            pass


# Pre-optimize imports if enabled
optimize_startup_imports()


# For compatibility with existing entry point configuration
if __name__ == "__main__":
    main()
