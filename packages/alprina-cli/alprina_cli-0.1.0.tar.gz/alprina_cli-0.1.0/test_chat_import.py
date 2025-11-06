#!/usr/bin/env python3
"""
Simple smoke test for chat module.
Tests if all components can be imported and initialized.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all chat-related modules can be imported."""
    print("Testing imports...")

    try:
        from alprina_cli.context_manager import ConversationContext
        print("✓ ConversationContext imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ConversationContext: {e}")
        return False

    try:
        from alprina_cli.chat import AlprinaChatSession
        print("✓ AlprinaChatSession imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import AlprinaChatSession: {e}")
        return False

    try:
        from alprina_cli.cai_agent_bridge import CAIAgentBridge
        print("✓ CAIAgentBridge imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import CAIAgentBridge: {e}")
        return False

    try:
        from alprina_cli.llm_provider import get_llm_client, LLMProvider
        print("✓ LLM provider imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import LLM provider: {e}")
        return False

    return True


def test_context_manager():
    """Test ConversationContext initialization."""
    print("\nTesting ConversationContext...")

    try:
        from alprina_cli.context_manager import ConversationContext

        ctx = ConversationContext(max_history=10)
        ctx.add_user_message("Test message")
        ctx.add_assistant_message("Test response")

        messages = ctx.get_messages_for_llm()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

        print("✓ ConversationContext works correctly")
        return True
    except Exception as e:
        print(f"✗ ConversationContext test failed: {e}")
        return False


def test_llm_provider():
    """Test LLM provider initialization (without actual API calls)."""
    print("\nTesting LLM provider...")

    try:
        from alprina_cli.llm_provider import LLMProvider

        # Just verify the enum exists
        providers = [p.value for p in LLMProvider]
        assert "openai" in providers
        assert "anthropic" in providers

        print(f"✓ LLM providers available: {', '.join(providers)}")
        return True
    except Exception as e:
        print(f"✗ LLM provider test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Alprina Chat Module Smoke Test")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("ConversationContext Test", test_context_manager),
        ("LLM Provider Test", test_llm_provider),
    ]

    results = []
    for name, test_func in tests:
        results.append(test_func())

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("\n🎉 All tests passed! Chat module is ready to use.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
