"""
seraa/cli/chat.py - Interactive chat CLI for SERAA
"""

import argparse
from ..llm.chat_agent import SeraaChat


def parse_custom_values(values_str: str) -> dict:
    """Parse custom values from command line string."""
    if not values_str:
        return {}
    
    values = {}
    for pair in values_str.split(','):
        key, val = pair.strip().split('=')
        values[key.strip()] = float(val.strip())
    
    return values


def main():
    parser = argparse.ArgumentParser(description="SERAA Interactive Chat Agent")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai", "anthropic"])
    parser.add_argument("--model", default="qwen2.5:1.5b", help="Model name")
    parser.add_argument("--domain", default="general", choices=["general", "government", "corporate", "tech"])
    parser.add_argument(
        "--framework",
        default="secular",
        choices=["secular", "christian", "buddhist", "ubuntu", "stoic", "virtue_ethics"],
        help="Ethical framework to apply"
    )
    parser.add_argument(
        "--values",
        default="",
        help="Custom moral weights (e.g., 'compassion=0.4,justice=0.3,wisdom=0.3')"
    )
    
    args = parser.parse_args()
    
    # Parse custom values
    custom_values = parse_custom_values(args.values)
    
    print("="*70)
    print("SERAA INTERACTIVE CHAT AGENT")
    print("="*70)
    print()
    
    # Initialize chat agent
    chat = SeraaChat(
        llm_backend=args.backend,
        model=args.model,
        seraa_domain=args.domain,
        custom_values=custom_values,
        ethical_framework=args.framework
    )
    
    print()
    print("="*70)
    print("Commands:")
    print("  - Type your ethical question or scenario")
    print("  - 'history' - View conversation history")
    print("  - 'weights' - View current moral weights")
    print("  - 'reset' - Clear conversation history")
    print("  - 'quit' or 'exit' - Exit chat")
    print("="*70)
    print()
    
    # Chat loop
    while True:
        try:
            user_input = input("\n🤔 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'history':
                print("\n" + chat.get_conversation_summary())
                continue
            
            if user_input.lower() == 'weights':
                print("\n**Current Moral Weights:**")
                print(chat._format_weights())
                continue
            
            if user_input.lower() == 'reset':
                chat.reset()
                continue
            
            # Process question
            print("\n🤖 SERAA: Analyzing...\n")
            result = chat.chat(user_input)
            print(result['chat_response'])
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}")


if __name__ == "__main__":
    main()
