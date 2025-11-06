#!/usr/bin/env python3
"""
Test basic chat functionality without full interactive session.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_chat_components():
    """Test individual chat components."""
    print("=" * 60)
    print("Testing Alprina Chat Components")
    print("=" * 60)

    # Test 1: Import chat module
    print("\n1. Testing chat module import...")
    try:
        from alprina_cli.chat import AlprinaChatSession
        print("✓ Chat module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import chat module: {e}")
        return False

    # Test 2: Check API key
    print("\n2. Checking API keys...")
    import os
    if os.getenv("ANTHROPIC_API_KEY"):
        print("✓ ANTHROPIC_API_KEY is set")
    else:
        print("✗ ANTHROPIC_API_KEY not found")
        return False

    # Test 3: Initialize chat session
    print("\n3. Initializing chat session...")
    try:
        session = AlprinaChatSession(
            model="claude-3-5-sonnet-20241022",
            streaming=False
        )
        print("✓ Chat session initialized")
    except Exception as e:
        print(f"✗ Failed to initialize chat session: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Test context manager
    print("\n4. Testing context manager...")
    try:
        session.context.add_user_message("Test message")
        session.context.add_assistant_message("Test response")
        messages = session.context.get_messages_for_llm()
        assert len(messages) == 2
        print(f"✓ Context manager works ({len(messages)} messages)")
    except Exception as e:
        print(f"✗ Context manager failed: {e}")
        return False

    # Test 5: Build system prompt
    print("\n5. Testing system prompt generation...")
    try:
        system_prompt = session._build_system_prompt()
        assert len(system_prompt) > 0
        print(f"✓ System prompt generated ({len(system_prompt)} chars)")
    except Exception as e:
        print(f"✗ System prompt generation failed: {e}")
        return False

    # Test 6: Test LLM client
    print("\n6. Testing LLM client...")
    try:
        test_messages = [{"role": "user", "content": "Say 'test successful' in exactly 2 words"}]
        response = session.llm.chat(
            messages=test_messages,
            system_prompt="You are a helpful assistant. Be concise.",
            max_tokens=50,
            temperature=0.7
        )
        print(f"✓ LLM client works")
        print(f"  Response: {response[:100]}...")
    except Exception as e:
        print(f"✗ LLM client failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! Chat is ready to use.")
    print("=" * 60)
    print("\nTo start interactive chat, run:")
    print("  alprina chat")
    print("\nOr with specific options:")
    print("  alprina chat --model claude-3-5-sonnet-20241022")
    print("  alprina chat --no-streaming")
    return True


if __name__ == "__main__":
    success = test_chat_components()
    sys.exit(0 if success else 1)
