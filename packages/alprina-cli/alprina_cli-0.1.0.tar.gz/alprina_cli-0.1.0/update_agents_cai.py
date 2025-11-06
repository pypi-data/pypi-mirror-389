"""
Script to update all Alprina agent wrappers with CAI integration.

This script adds CAI integration to agent wrappers, enabling them to use
real CAI agents when available, with fallback to mock implementations.
"""

import re
from pathlib import Path

# Agent mapping: wrapper file -> CAI agent name
AGENT_MAPPING = {
    "blue_teamer.py": "blueteam_agent",
    "dfir.py": "dfir",
    "network_analyzer.py": "network_traffic_analyzer",
    "reverse_engineer.py": "reverse_engineering_agent",
    "android_sast.py": "android_sast_agent",
    "memory_analysis.py": "memory_analysis_agent",
    "wifi_security.py": "wifi_security_tester",
    "replay_attack.py": "replay_attack_agent",
    "subghz_sdr.py": "subghz_sdr_agent",
    "retester.py": "retester",
    "mail.py": "mail",
    "guardrails.py": "guardrails"
}

# Template for CAI integration
CAI_INTEGRATION_TEMPLATE = '''"""
Alprina {agent_display_name}

{agent_description}
Integrated from CAI framework for use in Alprina platform.
"""

import asyncio
from typing import Dict, Any, List
from loguru import logger


# Import actual CAI {agent_display_name}
try:
    from cai.agents import get_agent_by_name
    CAI_AVAILABLE = True
    logger.info("CAI {agent_display_name} available")
except ImportError as e:
    CAI_AVAILABLE = False
    logger.warning(f"CAI agents not available: {{e}}")


class {class_name}Wrapper:
    """
    Wrapper for CAI {agent_display_name}.

    Provides synchronous interface to the async CAI agent.
    """

    def __init__(self):
        self.name = "{agent_display_name}"
        self.agent_type = "{agent_type}"
        self.description = "{agent_description}"
        self._cai_agent = None

    def _get_cai_agent(self):
        """Get or create CAI agent instance."""
        if not CAI_AVAILABLE:
            return None

        if self._cai_agent is None:
            try:
                # Get the real CAI agent
                self._cai_agent = get_agent_by_name("{cai_agent_name}")
                logger.info("CAI {agent_display_name} initialized")
            except Exception as e:
                logger.error(f"Failed to initialize CAI {agent_display_name}: {{e}}")
                return None

        return self._cai_agent

    async def _scan_async(self, target: str, safe_only: bool = True) -> Dict[str, Any]:
        """
        Async scan using real CAI agent.

        Args:
            target: Target system, application, or path
            safe_only: If True, only perform safe, non-destructive tests

        Returns:
            Dictionary with scan results
        """
        cai_agent = self._get_cai_agent()

        if cai_agent is None:
            # Fallback to mock implementation
            return self._mock_scan(target, safe_only)

        try:
            # Build prompt for CAI agent
            prompt = f"""Perform {agent_type} analysis on: {{target}}

Focus on:
{prompt_focus}

Provide detailed findings with severity levels."""

            # Create message for CAI agent
            messages = [
                {{"role": "user", "content": prompt}}
            ]

            # Run CAI agent (async)
            result = await cai_agent.run(messages)

            # Parse CAI agent response into findings
            findings = self._parse_cai_response(result.value, target)

            return {{
                "agent": self.name,
                "type": self.agent_type,
                "target": target,
                "findings": findings,
                "summary": {{
                    "total_findings": len(findings),
                    "cai_powered": True
                }}
            }}

        except Exception as e:
            logger.error(f"CAI {agent_display_name} error: {{e}}")
            # Fallback to mock
            return self._mock_scan(target, safe_only)

    def _mock_scan(self, target: str, safe_only: bool = True) -> Dict[str, Any]:
        """
        Mock scan implementation (fallback when CAI not available).

        Args:
            target: Target to scan
            safe_only: Only perform safe tests

        Returns:
            Mock scan results
        """
{mock_implementation}

    def _parse_cai_response(self, response: str, target: str) -> List[Dict[str, Any]]:
        """
        Parse CAI agent response into structured findings.

        Args:
            response: CAI agent response text
            target: Target that was scanned

        Returns:
            List of finding dictionaries
        """
        findings = []
        import re

        # Parse response text for findings
        high_pattern = r"(?i)(critical|high|severe).*?(?=\\n\\n|\\Z)"
        medium_pattern = r"(?i)(medium|moderate).*?(?=\\n\\n|\\Z)"
        low_pattern = r"(?i)(low|minor|info).*?(?=\\n\\n|\\Z)"

        for severity, pattern in [("HIGH", high_pattern), ("MEDIUM", medium_pattern), ("LOW", low_pattern)]:
            matches = re.finditer(pattern, response, re.DOTALL)
            for match in matches:
                finding_text = match.group(0)
                lines = finding_text.strip().split('\\n')
                title = lines[0] if lines else "Security Finding"

                finding = {{
                    "type": "{finding_type}",
                    "severity": severity,
                    "title": title[:100],
                    "description": finding_text[:500],
                    "file": target,
                    "line": 0,
                    "confidence": 0.8
                }}
                findings.append(finding)

        # If no findings parsed, create a summary finding
        if not findings and len(response) > 50:
            findings.append({{
                "type": "{finding_type}",
                "severity": "INFO",
                "title": "{agent_display_name} Analysis Complete",
                "description": response[:500],
                "file": target,
                "line": 0,
                "confidence": 1.0
            }})

        return findings

    def scan(self, target: str, safe_only: bool = True) -> Dict[str, Any]:
        """
        Perform security scan (synchronous wrapper).

        Args:
            target: Target system, application, or path
            safe_only: If True, only perform safe, non-destructive tests

        Returns:
            Dictionary with scan results
        """
        logger.info(f"{agent_display_name} scanning: {{target}} (safe_only={{safe_only}}, CAI={{CAI_AVAILABLE}})")

        # Run async scan in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._scan_async(target, safe_only))


# Create singleton instance
{instance_name} = {class_name}Wrapper()


def {function_name}(target: str, safe_only: bool = True) -> Dict[str, Any]:
    """
    Run security scan.

    Args:
        target: Target to scan
        safe_only: Only perform safe tests

    Returns:
        Scan results
    """
    return {instance_name}.scan(target, safe_only)
'''


def extract_mock_implementation(file_content: str) -> str:
    """Extract the mock implementation from existing file."""
    # Extract the scan method body
    scan_match = re.search(r'def scan\(self.*?\n(.*?)(?=\n\n|\nclass|\ndef\s|# Create singleton|$)',
                           file_content, re.DOTALL)
    if scan_match:
        body = scan_match.group(1)
        # Indent by 8 spaces (2 levels)
        lines = body.split('\n')
        indented = []
        for line in lines:
            if line.strip():
                # Remove first 8 spaces of indentation, then add 8 spaces
                dedented = line[8:] if line.startswith(' ' * 8) else line
                indented.append('        ' + dedented)
            else:
                indented.append('')
        return '\n'.join(indented)

    # Fallback mock
    return '''        findings = []
        findings.append({
            "type": "Security Finding",
            "severity": "INFO",
            "title": "Mock scan result",
            "description": "This is a mock implementation. Enable CAI for real analysis.",
            "file": target,
            "line": 0,
            "confidence": 0.5
        })

        return {
            "agent": self.name,
            "type": self.agent_type,
            "target": target,
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "cai_powered": False
            }
        }'''


def update_agent_file(file_path: Path, cai_agent_name: str):
    """Update an agent file with CAI integration."""
    print(f"Updating {file_path.name}...")

    # Read existing file
    content = file_path.read_text()

    # Extract metadata
    class_match = re.search(r'class (\w+Agent):', content)
    instance_match = re.search(r'(\w+_agent) = \w+Agent\(\)', content)
    function_match = re.search(r'def (run_\w+_scan)\(', content)

    if not class_match or not instance_match or not function_match:
        print(f"  ⚠️  Skipping {file_path.name} - couldn't extract metadata")
        return False

    class_name = class_match.group(1).replace('Agent', '')
    instance_name = instance_match.group(1)
    function_name = function_match.group(1)

    # Extract agent display name from docstring
    doc_match = re.search(r'""".*?Alprina ([^\n]+)\n', content, re.DOTALL)
    agent_display_name = doc_match.group(1) if doc_match else class_name

    # Extract description
    desc_match = re.search(r'self.description = "(.*?)"', content)
    agent_description = desc_match.group(1) if desc_match else "Security analysis agent"

    # Extract agent type
    type_match = re.search(r'self.agent_type = "(.*?)"', content)
    agent_type = type_match.group(1) if type_match else "security-analysis"

    # Extract mock implementation
    mock_impl = extract_mock_implementation(content)

    # Determine prompt focus based on agent type
    prompt_focuses = {
        "defensive-security": "- Security controls\n- Defense gaps\n- Threat detection\n- Incident response capabilities",
        "forensics": "- Digital forensics\n- Evidence collection\n- Timeline reconstruction\n- Indicators of compromise",
        "network-analysis": "- Network traffic patterns\n- Protocol analysis\n- Suspicious connections\n- Network vulnerabilities",
        "binary-analysis": "- Binary reverse engineering\n- Malware analysis\n- Code decompilation\n- Security bypasses",
        "android-scan": "- Android security issues\n- APK analysis\n- Permission abuse\n- Malicious behavior",
        "memory-forensics": "- Memory forensics\n- Runtime analysis\n- Process inspection\n- Malware artifacts",
        "wifi-test": "- WiFi security\n- Wireless vulnerabilities\n- Encryption weaknesses\n- Rogue access points",
        "replay-check": "- Replay attack vectors\n- Session token reuse\n- Authentication bypass\n- Timing vulnerabilities",
        "radio-security": "- RF security\n- SDR analysis\n- Signal interception\n- Wireless protocols",
        "retest": "- Vulnerability verification\n- Fix validation\n- Regression testing\n- Security posture improvement",
        "email-report": "- Email security\n- Phishing indicators\n- Malicious attachments\n- SPF/DKIM/DMARC",
        "safety-check": "- Security guardrails\n- Safe operation validation\n- Risk assessment\n- Compliance checks"
    }
    prompt_focus = prompt_focuses.get(agent_type, "- Security analysis\n- Vulnerability detection\n- Risk assessment\n- Best practices")

    # Determine finding type
    finding_types = {
        "defensive-security": "Defense Gap",
        "forensics": "Forensic Finding",
        "network-analysis": "Network Issue",
        "binary-analysis": "Binary Analysis",
        "android-scan": "Android Vulnerability",
        "memory-forensics": "Memory Artifact",
        "wifi-test": "WiFi Security Issue",
        "replay-check": "Replay Vulnerability",
        "radio-security": "RF Security Issue",
        "retest": "Validation Result",
        "email-report": "Email Security Issue",
        "safety-check": "Safety Check"
    }
    finding_type = finding_types.get(agent_type, "Security Finding")

    # Generate new content
    new_content = CAI_INTEGRATION_TEMPLATE.format(
        agent_display_name=agent_display_name,
        agent_description=agent_description,
        class_name=class_name,
        agent_type=agent_type,
        cai_agent_name=cai_agent_name,
        prompt_focus=prompt_focus,
        mock_implementation=mock_impl,
        finding_type=finding_type,
        instance_name=instance_name,
        function_name=function_name
    )

    # Write updated file
    file_path.write_text(new_content)
    print(f"  ✅ Updated {file_path.name}")
    return True


def main():
    """Update all agent files."""
    agents_dir = Path(__file__).parent / "src" / "alprina_cli" / "agents"

    print("🔧 Updating Alprina agent wrappers with CAI integration...\n")

    updated = 0
    skipped = 0

    for filename, cai_agent_name in AGENT_MAPPING.items():
        file_path = agents_dir / filename

        if not file_path.exists():
            print(f"  ⚠️  {filename} not found, skipping")
            skipped += 1
            continue

        if update_agent_file(file_path, cai_agent_name):
            updated += 1
        else:
            skipped += 1

    print(f"\n✅ Update complete: {updated} agents updated, {skipped} skipped")


if __name__ == "__main__":
    main()
