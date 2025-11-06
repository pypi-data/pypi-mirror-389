# Claude Code Guidelines

## Python Code Standards

### Import Rules

**HARD RULE: Never import libraries inside functions or classes.**

All imports must be at the top of the module, following PEP 8 conventions:

```python
# ✅ CORRECT
import re
from fastapi import HTTPException

from mosaygent.command_runner import run_command


async def flutter_version() -> str:
    version_match = re.search(r'(\d+\.\d+\.\d+)', output)
    if not version_match:
        raise HTTPException(status_code=500, detail="Parse error")
    return version_match.group(1)
```

```python
# ❌ WRONG
async def flutter_version() -> str:
    import re  # NEVER DO THIS
    from fastapi import HTTPException  # NEVER DO THIS

    version_match = re.search(r'(\d+\.\d+\.\d+)', output)
    return version_match.group(1)
```

**Import Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports (always use absolute paths)

### Import Path Rules

**Always use absolute imports, never relative imports.**

```python
# ✅ CORRECT
from mosaygent.command_runner import run_command
from mosaygent.services.email.resend_service import send_email

# ❌ WRONG
from .command_runner import run_command
from ..services.email.resend_service import send_email
```

### Logging Rules

**Log often, log plenty. Include logging wherever it makes sense, do so generously.**

Logging is critical for debugging, monitoring, and understanding system behavior in production. When in doubt, add a log statement.

**Standard logger pattern (use this in every module):**
```python
from mosaygent.logger import get_logger

logger = get_logger(__name__)
```

**Example with generous logging:**
```python
from mosaygent.logger import get_logger

logger = get_logger(__name__)


async def flutter_version() -> str:
    """Get the locally installed Flutter version."""
    logger.info("Fetching Flutter version")

    try:
        result = await run_command(['flutter', '--version'], timeout=10)
        logger.debug(f"Flutter command output: {result.stdout[:100]}")

        version_match = re.search(r'Flutter\s+(\d+\.\d+\.\d+)', result.stdout)
        if version_match:
            version = version_match.group(1)
            logger.info(f"Successfully parsed Flutter version: {version}")
            return version

        logger.warning("Could not parse Flutter version with primary pattern, trying fallback")
        version_match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
        if version_match:
            version = version_match.group(1)
            logger.info(f"Parsed Flutter version with fallback pattern: {version}")
            return version

        logger.error(f"Failed to parse Flutter version from output: {result.stdout}")
        raise HTTPException(status_code=500, detail="Could not parse Flutter version")
    except Exception as e:
        logger.exception(f"Error fetching Flutter version: {e}")
        raise
```

**Log at appropriate levels:**
- `logger.debug()` - Detailed diagnostic info (verbose details)
- `logger.info()` - General informational messages (operations, success states)
- `logger.warning()` - Warning messages (degraded state, fallbacks, retries)
- `logger.error()` - Error messages (failures that are handled)
- `logger.exception()` - Error with full stack trace (use in except blocks)

**What to log:**
- Function entry points (especially for API endpoints)
- Important state changes
- External command execution and results
- Fallback logic and retries
- Errors and exceptions (always use `logger.exception()` in except blocks)
- Performance-critical operations (with timing if relevant)
- Any decision points or branching logic

### Code Comments

**Don't add comments in the code unless pointing out something important or unique. Code should be self-documenting.**

Use descriptive names for functions, variables, and classes. Only add comments for non-obvious behavior, workarounds, or critical context.

Docstrings are always encouraged and should be used for all public functions, classes, and modules.

```python
# ✅ CORRECT - Self-documenting code with concise docstrings
async def parse_flutter_version(output: str) -> str:
    """Extract semantic version (X.Y.Z) from Flutter CLI output."""
    version_match = re.search(r'Flutter\s+(\d+\.\d+\.\d+)', output)
    if version_match:
        return version_match.group(1)

    version_match = re.search(r'(\d+\.\d+\.\d+)', output)
    if version_match:
        return version_match.group(1)

    raise HTTPException(status_code=500, detail="Could not parse Flutter version")


# ❌ WRONG - Over-commented code
async def parse_flutter_version(output: str) -> str:
    # Search for the version in the output
    version_match = re.search(r'Flutter\s+(\d+\.\d+\.\d+)', output)

    # If we found a match, return it
    if version_match:
        # Extract group 1 from the regex match
        return version_match.group(1)

    # Try a fallback pattern
    version_match = re.search(r'(\d+\.\d+\.\d+)', output)

    # Check if the fallback worked
    if version_match:
        # Return the matched version
        return version_match.group(1)

    # Raise an error if we couldn't find the version
    raise HTTPException(status_code=500, detail="Could not parse Flutter version")
```

**When to use comments:**
- Explaining WHY, not WHAT (the code already shows what)
- Documenting workarounds or non-obvious solutions
- Marking TODOs, FIXMEs, or technical debt
- Explaining complex algorithms or business logic
- Noting important assumptions or constraints
- Referencing external documentation or ticket numbers

**Always use docstrings for:**
- All public functions, methods, and classes
- Module-level documentation
- Complex private functions that would benefit from explanation

**Docstring style:**
- Keep them short and concise (one line when possible)
- Use extended format only when parameters/returns need clarification
- Focus on what the function does, not how it does it

### Dependency Management

**Remove unused dependencies whenever you see one.**

Keep imports clean and remove any that are not being used. This improves code clarity, reduces bundle size, and prevents confusion.

```python
# ✅ CORRECT - Only necessary imports
import re

from fastapi import APIRouter, HTTPException

from mosaygent.command_runner import run_command


@router.get("/flutter-version")
async def flutter_version() -> str:
    """Get locally installed Flutter version."""
    result = await run_command(['flutter', '--version'], timeout=10)
    version_match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
    if version_match:
        return version_match.group(1)
    raise HTTPException(status_code=500, detail="Could not parse version")


# ❌ WRONG - Unused imports
import re
import json  # Not used
from typing import Optional  # Not used

from fastapi import APIRouter, HTTPException, Depends  # Depends not used

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger  # Not used


@router.get("/flutter-version")
async def flutter_version() -> str:
    """Get locally installed Flutter version."""
    result = await run_command(['flutter', '--version'], timeout=10)
    version_match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
    if version_match:
        return version_match.group(1)
    raise HTTPException(status_code=500, detail="Could not parse version")
```

**When reviewing code:**
- Scan imports and verify each is actually used
- Remove any import that isn't referenced in the file
- Use IDE tools or linters to detect unused imports automatically

### API Response Design

**"status" is never necessary in the output body. It should always be passed as the HTTP status code.**

Use proper HTTP status codes to communicate success or failure. Don't include redundant "status" fields in the response body.

```python
# ✅ CORRECT - Status communicated via HTTP status code
@router.get("/flutter-version")
async def flutter_version() -> dict:
    """Get locally installed Flutter version information."""
    result = await run_command(['flutter', '--version'], timeout=10)
    version = parse_version(result.stdout)

    return {
        "version": version,
        "path": "/usr/bin/flutter",
        "full_output": result.stdout
    }
    # HTTP 200 OK is implicit for successful returns


# ✅ CORRECT - Error with proper status code
@router.get("/flutter-version")
async def flutter_version() -> dict:
    """Get locally installed Flutter version information."""
    result = await run_command(['flutter', '--version'], timeout=10)

    if not result.success:
        raise HTTPException(
            status_code=500,  # Status in HTTP header
            detail="Could not parse Flutter version"
        )

    return {"version": parse_version(result.stdout)}


# ❌ WRONG - Redundant status in body
@router.get("/flutter-version")
async def flutter_version() -> dict:
    """Get locally installed Flutter version information."""
    result = await run_command(['flutter', '--version'], timeout=10)
    version = parse_version(result.stdout)

    return {
        "status": "success",  # NEVER DO THIS
        "version": version,
        "path": "/usr/bin/flutter"
    }
```

**HTTP status codes to use:**
- `200 OK` - Successful GET, PUT, PATCH (implicit on return)
- `201 Created` - Successful POST that creates a resource
- `204 No Content` - Successful DELETE or action with no response body
- `400 Bad Request` - Invalid input/validation error
- `404 Not Found` - Resource or command not found
- `408 Request Timeout` - Operation timed out
- `500 Internal Server Error` - Unexpected server error

### Testing Standards

**Use function-based tests, NOT class-based tests.**

Organize tests using simple functions, not test classes.

```python
# ✅ CORRECT - Function-based tests
@pytest.mark.asyncio
async def test_command_runs_successfully():
    """Test that commands execute successfully."""
    result = await run_command(['echo', 'hello'])
    assert result.success


@pytest.mark.asyncio
async def test_command_not_found():
    """Test command not found raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        await run_command(['nonexistent_command'])
    assert exc_info.value.status_code == 404


# ❌ WRONG - Class-based tests
class TestRunCommand:
    @pytest.mark.asyncio
    async def test_command_runs_successfully(self):
        result = await run_command(['echo', 'hello'])
        assert result.success

    @pytest.mark.asyncio
    async def test_command_not_found(self):
        with pytest.raises(HTTPException):
            await run_command(['nonexistent_command'])
```

**Keep tests minimal:**
- Test the happy path
- Test the main error cases
- Don't over-test every edge case
- Tests should demonstrate the framework works
