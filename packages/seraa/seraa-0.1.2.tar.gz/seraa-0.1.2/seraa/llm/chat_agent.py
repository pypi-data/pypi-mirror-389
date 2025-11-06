"""
seraa/llm/chat_agent.py - Interactive chat interface for SERAA ethical agent
"""

from typing import Dict, Any, List, Optional
from .ethical_agent import EthicalLLMAgent


class SeraaChat:
    """
    Interactive chat interface for SERAA ethical evaluations.
    
    Allows conversational interaction and maintains context.
    """
    
    def __init__(
        self,
        llm_backend: str = "ollama",
        model: str = "qwen2.5:1.5b",
        seraa_domain: str = "general",
        custom_values: Optional[Dict[str, float]] = None,
        ethical_framework: str = "secular"
    ):
        """
        Initialize chat agent.
        
        Args:
            llm_backend: LLM backend to use
            model: Model name
            seraa_domain: Domain configuration
            custom_values: User's custom moral weights
            ethical_framework: Ethical tradition (secular, christian, buddhist, ubuntu, stoic, virtue_ethics)
        """
        self.agent = EthicalLLMAgent(llm_backend, model, seraa_domain)
        self.ethical_framework = ethical_framework
        self.custom_values = custom_values or {}
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Apply custom value system if provided
        if custom_values:
            self._apply_custom_values(custom_values)
        
        # Apply framework-specific adjustments
        self._apply_framework(ethical_framework)
        
        print(f"✓ Chat Agent Ready")
        print(f"  Ethical Framework: {ethical_framework}")
        if custom_values:
            print(f"  Custom Values: {list(custom_values.keys())}")
    
    def _apply_custom_values(self, custom_values: Dict[str, float]):
        """Apply user's custom moral weights to SERAA agent."""
        # Merge with existing weights
        current_weights = self.agent.seraa.moral_state.weights.copy()
        current_weights.update(custom_values)
        
        # Normalize
        total = sum(current_weights.values())
        if total > 0:
            normalized = {k: v/total for k, v in current_weights.items()}
            self.agent.seraa.moral_state.weights = normalized
    
    def _apply_framework(self, framework: str):
        """Apply ethical framework-specific adjustments."""
        
        frameworks = {
            'christian': {
                'weights': {'compassion': 0.3, 'dignity': 0.25, 'justice': 0.25, 'stewardship': 0.2},
                'core_values': {'human_dignity': 1.0, 'sanctity_of_life': 1.0, 'love_of_neighbor': 0.9}
            },
            'buddhist': {
                'weights': {'compassion': 0.35, 'non_harm': 0.3, 'mindfulness': 0.2, 'interdependence': 0.15},
                'core_values': {'reduce_suffering': 1.0, 'right_action': 0.9, 'interconnection': 0.9}
            },
            'ubuntu': {
                'weights': {'community': 0.4, 'compassion': 0.25, 'dignity': 0.2, 'solidarity': 0.15},
                'core_values': {'personhood_through_others': 1.0, 'collective_wellbeing': 1.0}
            },
            'stoic': {
                'weights': {'wisdom': 0.3, 'justice': 0.3, 'courage': 0.2, 'temperance': 0.2},
                'core_values': {'virtue': 1.0, 'reason': 0.9, 'acceptance': 0.8}
            },
            'virtue_ethics': {
                'weights': {'practical_wisdom': 0.3, 'justice': 0.25, 'courage': 0.25, 'temperance': 0.2},
                'core_values': {'human_flourishing': 1.0, 'character': 0.9}
            },
            'secular': {
                'weights': {'fairness': 0.3, 'autonomy': 0.25, 'transparency': 0.25, 'care': 0.2},
                'core_values': {'human_dignity': 1.0, 'agency_preservation': 1.0}
            }
        }
        
        if framework in frameworks:
            config = frameworks[framework]
            self.agent.seraa.moral_state.weights = config['weights']
            self.agent.seraa.core_values = config['core_values']
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and return evaluation.
        
        Args:
            user_input: User's ethical question or scenario
            
        Returns:
            Evaluation result with conversational response
        """
        # Evaluate the question
        result = self.agent.evaluate_question(user_input)
        
        # Add to conversation history
        self.conversation_history.append({
            'user': user_input,
            'result': result,
            'framework': self.ethical_framework
        })
        
        # Generate conversational response
        response = self._format_chat_response(result)
        result['chat_response'] = response
        
        return result
    
    def _format_chat_response(self, result: Dict[str, Any]) -> str:
        """Format evaluation as natural conversation."""
        
        verdict_emoji = "✅" if result['verdict'] == 'APPROVED' else "⚠️"
        verdict_text = "ethically acceptable" if result['verdict'] == 'APPROVED' else "ethically problematic"
        
        response = f"""{verdict_emoji} From a {self.ethical_framework} perspective, this scenario is {verdict_text}.

**PAC Score:** {result['pac_score']:.2f}/1.0

**Analysis:**
{result['explanation']}

**Moral Weights Applied:**
{self._format_weights()}
"""
        
        if result['violations']:
            response += f"\n**Constraints Violated:** {', '.join(result['violations'])}"
        
        return response
    
    def _format_weights(self) -> str:
        """Format current moral weights for display."""
        weights = self.agent.seraa.moral_state.weights
        return "\n".join([f"  • {k}: {v:.2f}" for k, v in sorted(weights.items(), key=lambda x: -x[1])])
    
    def get_conversation_summary(self) -> str:
        """Get summary of conversation history."""
        if not self.conversation_history:
            return "No conversation history yet."
        
        summary = f"**Conversation History ({len(self.conversation_history)} evaluations)**\n\n"
        for i, entry in enumerate(self.conversation_history, 1):
            verdict = "✅" if entry['result']['verdict'] == 'APPROVED' else "⚠️"
            summary += f"{i}. {verdict} {entry['user'][:60]}...\n"
        
        return summary
    
    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []
        print("✓ Conversation history cleared")
