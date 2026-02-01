"""Integration test to verify skill scripts are actually invoked.

This test validates that when an LLM is asked to use a skill script,
the script is actually executed and the result is not hallucinated.

We use math operations that LLMs consistently get wrong (like 23!)
but Python computes trivially. If the exact answer appears in the
response, the script was invoked.
"""

import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest

# Test configuration
SOLIPLEX_URL = os.environ.get("SOLIPLEX_URL", "http://127.0.0.1:8002")
ROOM_ID = "code-reviewer"  # Room with skills enabled
TIMEOUT = 120  # LLM response timeout in seconds


def compute_expected_answers() -> dict:
    """Pre-compute expected answers for verification."""
    return {
        "factorial_23": str(math.factorial(23)),  # 25852016738884976640000
        "fibonacci_47": "2971215073",  # fib(47)
        "multiply": str(8734 * 9821),  # 85776614
        "modexp": str(pow(7, 23, 13)),  # 2
    }


@pytest.fixture(scope="module")
def expected_answers():
    """Fixture providing expected mathematical results."""
    return compute_expected_answers()


@pytest.fixture(scope="module")
def soliplex_available():
    """Check if Soliplex server is running."""
    try:
        response = httpx.get(f"{SOLIPLEX_URL}/api/ok", timeout=5)
        return response.status_code == 200
    except httpx.RequestError:
        return False


def send_message_and_wait(room_id: str, message: str, timeout: int = TIMEOUT) -> str | None:
    """Send message to room and wait for complete response.

    Uses AG-UI protocol two-step flow:
    1. POST to create thread/run
    2. POST with RunAgentInput to execute (streams SSE events)

    Returns the assistant's response text, or None if failed.
    """
    try:
        # Step 1: Create thread and run
        create_payload = {
            "thread_id": f"test-{hashlib.md5(message.encode()).hexdigest()[:8]}",
            "messages": [{"id": "msg-1", "role": "user", "content": message}],
        }
        create_response = httpx.post(
            f"{SOLIPLEX_URL}/api/v1/rooms/{room_id}/agui",
            json=create_payload,
            timeout=10,
        )
        create_response.raise_for_status()
        create_data = create_response.json()

        thread_id = create_data["thread_id"]
        run_id = list(create_data["runs"].keys())[0]

        # Step 2: Execute run with AG-UI RunAgentInput
        exec_payload = {
            "threadId": thread_id,
            "runId": run_id,
            "state": {},
            "messages": [{"id": "msg-1", "role": "user", "content": message}],
            "tools": [],
            "context": [],
            "forwardedProps": {},
        }

        # Stream the response and collect text
        response_text = []
        with httpx.stream(
            "POST",
            f"{SOLIPLEX_URL}/api/v1/rooms/{room_id}/agui/{thread_id}/{run_id}",
            json=exec_payload,
            headers={"Accept": "text/event-stream"},
            timeout=timeout,
        ) as response:
            for line in response.iter_lines():
                if line and line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        # Collect text content from assistant messages
                        if event.get("type") == "TEXT_MESSAGE_CONTENT":
                            delta = event.get("delta", "")
                            response_text.append(delta)
                        # Also check for tool results
                        elif event.get("type") == "TOOL_RESULT":
                            result = event.get("result", "")
                            response_text.append(str(result))
                    except json.JSONDecodeError:
                        pass

        return "".join(response_text) if response_text else None

    except httpx.RequestError as e:
        pytest.skip(f"Soliplex request failed: {e}")
        return None


class TestMathSkillScript:
    """Unit tests for the math-solver script directly."""

    @pytest.fixture
    def script_path(self):
        """Path to the calculate.py script."""
        return Path(__file__).parent.parent / "example/skills/math-solver/scripts/calculate.py"

    def run_script(self, script_path: Path, *args: str) -> str:
        """Run the script and return output."""
        result = subprocess.run(
            ["python3", str(script_path), *args],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_factorial_23(self, script_path, expected_answers):
        """Test factorial computation."""
        output = self.run_script(script_path, "factorial", "23")
        assert expected_answers["factorial_23"] in output

    def test_fibonacci_47(self, script_path, expected_answers):
        """Test fibonacci computation."""
        output = self.run_script(script_path, "fibonacci", "47")
        assert expected_answers["fibonacci_47"] in output

    def test_multiply(self, script_path, expected_answers):
        """Test multiplication."""
        output = self.run_script(script_path, "multiply", "8734", "9821")
        assert expected_answers["multiply"] in output

    def test_modexp(self, script_path, expected_answers):
        """Test modular exponentiation."""
        output = self.run_script(script_path, "modexp", "7", "23", "13")
        assert expected_answers["modexp"] in output


@pytest.mark.integration
@pytest.mark.slow
class TestMathSkillIntegration:
    """Integration tests verifying skill scripts are actually invoked by LLM.

    These tests send messages to a Soliplex room and verify that the
    exact computed answer appears in the response - proving the script
    was actually executed rather than the LLM hallucinating.

    Skip these tests if Soliplex is not running:
        pytest -m "not integration"

    Run only these tests:
        pytest -m integration
    """

    def test_factorial_not_hallucinated(self, soliplex_available, expected_answers):
        """Verify 23! is computed by script, not hallucinated.

        LLMs almost never get 23! correct. If the exact answer appears,
        the script was invoked.
        """
        if not soliplex_available:
            pytest.skip("Soliplex server not available")

        prompt = """You have the math-solver skill available.
Use the run_skill_script tool to execute calculate.py with operation 'factorial' and argument '23'.
Return ONLY the exact numerical result."""

        response = send_message_and_wait(ROOM_ID, prompt)

        if response is None:
            pytest.skip("No response received (timeout or error)")

        expected = expected_answers["factorial_23"]
        assert expected in response, (
            f"Expected factorial result '{expected}' not found in response. "
            f"LLM may have hallucinated. Response: {response[:500]}"
        )

    def test_fibonacci_not_hallucinated(self, soliplex_available, expected_answers):
        """Verify fib(47) is computed by script, not hallucinated."""
        if not soliplex_available:
            pytest.skip("Soliplex server not available")

        prompt = """You have the math-solver skill available.
Use the run_skill_script tool to execute calculate.py with operation 'fibonacci' and argument '47'.
Return ONLY the exact numerical result."""

        response = send_message_and_wait(ROOM_ID, prompt)

        if response is None:
            pytest.skip("No response received (timeout or error)")

        expected = expected_answers["fibonacci_47"]
        assert expected in response, (
            f"Expected fibonacci result '{expected}' not found in response. "
            f"LLM may have hallucinated. Response: {response[:500]}"
        )


class TestSkillDiscovery:
    """Test that math-solver skill is properly discovered."""

    def test_skill_exists(self):
        """Verify math-solver skill directory structure."""
        skill_dir = Path(__file__).parent.parent / "example/skills/math-solver"
        assert skill_dir.exists(), "math-solver skill directory not found"
        assert (skill_dir / "SKILL.md").exists(), "SKILL.md not found"
        assert (skill_dir / "scripts/calculate.py").exists(), "calculate.py not found"

    def test_skill_discovered(self):
        """Verify math-solver is discovered by pydantic-ai-skills."""
        pytest.importorskip("pydantic_ai_skills")
        from pydantic_ai_skills import discover_skills

        skills_dir = Path(__file__).parent.parent / "example/skills"
        discovered = discover_skills(skills_dir)
        skill_names = [s.name for s in discovered]

        assert "math-solver" in skill_names, (
            f"math-solver not in discovered skills: {skill_names}"
        )
