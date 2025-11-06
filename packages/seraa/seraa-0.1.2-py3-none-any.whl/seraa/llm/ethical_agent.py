"""
seraa/llm/ethical_agent.py - LLM-augmented ethical reasoning

Combines language models with SERAA framework for natural language ethics.
Optimized for local models (Qwen, Phi, Llama, etc.)
"""

import json
import re
from typing import Dict, Any
from ..core.agent import SeraaAgent
from ..axioms import EthicalConstraint


def robust_parse_json(text: str) -> Dict[str, Any]:
    """
    Robustly parse JSON from LLM output, handling common issues.
    Falls back to sensible defaults if parsing fails.
    """
    # Try to extract JSON block
    match = re.search(r'(\{[^}]*\})', text, re.DOTALL)
    if match:
        json_str = match.group(1)
        
        # Try parsing as-is
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Try common fixes
        try:
            # Replace single quotes with double quotes
            fixed = json_str.replace("'", '"')
            # Remove trailing commas
            fixed = re.sub(r',\s*}', '}', fixed)
            fixed = re.sub(r',\s*]', ']', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON parse error: {e}")
    
    # Fallback defaults
    print("  ⚠ Using fallback parameters")
    return {
        "actor": "Unknown",
        "stakeholders": ["affected parties"],
        "decision": text[:80] if text else "Unknown",
        "pac_score": 0.5,
        "transparency": 0.5,
        "consent_obtained": False,
        "harm_level": 2
    }


class EthicalLLMAgent:
    """
    Hybrid LLM + SERAA agent for ethical reasoning.
    
    Optimized for local models with robust fallbacks.
    """
    
    def __init__(
        self,
        llm_backend: str = "ollama",
        model: str = "qwen2.5:1.5b",
        seraa_domain: str = "general"
    ):
        """Initialize ethical LLM agent."""
        self.llm_backend = llm_backend
        self.model = model
        
        # Initialize SERAA agent
        self.seraa = self._create_seraa_agent(seraa_domain)
        
        print(f"✓ Ethical LLM Agent initialized")
        print(f"  LLM Backend: {llm_backend} ({model})")
        print(f"  SERAA Domain: {seraa_domain}")
    
    def _create_seraa_agent(self, domain: str) -> SeraaAgent:
        """Create SERAA agent with domain-specific configuration."""
        
        domain_configs = {
            'general': {
                'weights': {'fairness': 0.3, 'transparency': 0.25, 'autonomy': 0.25, 'care': 0.2},
                'threshold': 0.6
            },
            'government': {
                'weights': {'public_welfare': 0.35, 'transparency': 0.3, 'legal_compliance': 0.2, 'democracy': 0.15},
                'threshold': 0.65
            },
            'corporate': {
                'weights': {'stakeholder_welfare': 0.3, 'transparency': 0.3, 'sustainability': 0.2, 'legal_compliance': 0.2},
                'threshold': 0.65
            },
            'tech': {
                'weights': {'user_privacy': 0.35, 'transparency': 0.3, 'user_autonomy': 0.25, 'social_impact': 0.1},
                'threshold': 0.7
            }
        }
        
        config = domain_configs.get(domain, domain_configs['general'])
        
        agent = SeraaAgent(
            name=f"{domain}_ethics",
            moral_weights=config['weights'],
            core_values={'human_dignity': 1.0, 'agency_preservation': 1.0},
            pac_threshold=config['threshold']
        )
        
        # Add universal constraints
        agent.add_constraint(
            EthicalConstraint(
                "pac_minimum",
                lambda a: a.get('pac_score', 0) >= config['threshold'],
                f"PAC score below {config['threshold']}"
            )
        )
        
        agent.add_constraint(
            EthicalConstraint(
                "unjustified_harm",
                lambda a: a.get('harm_level', 0) == 0 or a.get('pac_score', 0) >= 0.7,
                "Unjustified harm to stakeholders"
            )
        )
        
        return agent
    
    def evaluate_question(self, question: str) -> Dict[str, Any]:
        """Evaluate an ethical question through LLM + SERAA pipeline."""
        print(f"\n{'='*70}")
        print(f"EVALUATING: {question}")
        print(f"{'='*70}")
        
        # Step 1: Extract parameters
        print("\n[1/3] Extracting ethical parameters...")
        params = self._extract_parameters(question)
        
        print(f"  ✓ Actor: {params.get('actor', 'Unknown')}")
        print(f"  ✓ PAC Score: {params.get('pac_score', 0.5):.2f}")
        print(f"  ✓ Harm Level: {params.get('harm_level', 0)}")
        
        # Step 2: SERAA evaluation
        print("\n[2/3] Running SERAA evaluation...")
        seraa_result = self.seraa.evaluate_action(params)
        verdict = "✅ ETHICALLY ACCEPTABLE" if seraa_result.approved else "⚠️ ETHICALLY PROBLEMATIC"
        print(f"  {verdict}")
        
        # Step 3: Generate explanation
        print("\n[3/3] Generating explanation...")
        explanation = self._generate_explanation(question, params, seraa_result)
        
        result = {
            'question': question,
            'verdict': 'APPROVED' if seraa_result.approved else 'REJECTED',
            'pac_score': params.get('pac_score', 0.5),
            'parameters': params,
            'seraa_result': seraa_result,
            'explanation': explanation,
            'constraints_satisfied': seraa_result.constraints_satisfied,
            'violations': [v.constraint_name for v in seraa_result.constraint_violations]
        }
        
        return result
    
    def _extract_parameters(self, question: str) -> Dict[str, Any]:  # ← FIXED INDENTATION
        """Extract ethical parameters using LLM with detailed scoring guidance."""
        
        extraction_prompt = f"""Analyze this ethical scenario and respond with ONLY a JSON object.

Question: {question}

Scoring Guidelines:
- pac_score (0.0-1.0): How much choice/agency people have
  * 0.9-1.0: Full informed consent, clear alternatives, reversible
  * 0.7-0.8: Good transparency, meaningful choices available
  * 0.5-0.6: Limited options, some coercion or unclear process
  * 0.3-0.4: Minimal agency, strong pressure or deception
  * 0.0-0.2: No real choice, forced compliance

- transparency (0.0-1.0): How open/clear the process is
  * 1.0: Fully disclosed, documented, accessible
  * 0.5: Partially hidden, unclear terms
  * 0.0: Secret, deceptive, opaque

- harm_level (0-5): Severity of potential negative impact
  * 0: No harm
  * 1: Minor inconvenience
  * 2: Moderate impact (privacy, time, money)
  * 3: Significant harm (health, freedom, livelihood)
  * 4: Severe harm (safety, rights, well-being)
  * 5: Critical/irreversible harm

JSON format:
{{
"actor": "who makes the decision",
"stakeholders": ["list of affected parties"],
"decision": "brief description of action",
"pac_score": 0.0,
"transparency": 0.0,
"consent_obtained": false,
"harm_level": 0
}}

Respond with ONLY the JSON, no explanation:"""

        llm_response = self._call_llm(extraction_prompt)
        params = robust_parse_json(llm_response)
        
        # Validate and bound numeric values
        params['pac_score'] = max(0.0, min(1.0, float(params.get('pac_score', 0.5))))
        params['transparency'] = max(0.0, min(1.0, float(params.get('transparency', 0.5))))
        params['harm_level'] = max(0, min(5, int(params.get('harm_level', 2))))
        
        return params
    
    def _generate_explanation(  # ← FIXED INDENTATION
        self,
        question: str,
        params: Dict[str, Any],
        seraa_result
    ) -> str:
        """Generate human-readable explanation using LLM."""
        
        violations = [v.constraint_name for v in seraa_result.constraint_violations]
        violation_text = f"\nViolations: {', '.join(violations)}" if violations else ""
        
        explanation_prompt = f"""Provide a brief 2-3 sentence ethical analysis:

Scenario: {question}
PAC Score: {params.get('pac_score', 0.5):.2f}/1.0
Verdict: {"APPROVED" if seraa_result.approved else "REJECTED"}{violation_text}

Explain why this {"preserves" if seraa_result.approved else "violates"} human agency and what could improve it.

Response:"""

        explanation = self._call_llm(explanation_prompt)
        return explanation.strip()
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM backend."""
        
        if self.llm_backend == "ollama":
            return self._call_ollama(prompt)
        elif self.llm_backend == "openai":
            return self._call_openai(prompt)
        elif self.llm_backend == "anthropic":
            return self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported LLM backend: {self.llm_backend}")
    
    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama API with timeout handling."""
        try:
            import requests
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 256  # Limit output length
                    }
                },
                timeout=90  # Increased timeout
            )
            
            # Parse response
            data = response.json()
            
            # Check for error
            if 'error' in data:
                print(f"  ⚠ Ollama error: {data['error']}")
                return f"Error: {data['error']}"
            
            # Check for response key
            if 'response' not in data:
                print(f"  ⚠ Unexpected Ollama format: {list(data.keys())}")
                return ""
            
            return data['response']
            
        except ImportError:
            return "Error: 'requests' library not installed. Run: pip install requests"
        except Exception as e:
            print(f"  ⚠ Ollama error: {type(e).__name__}")
            return f"Error: {type(e).__name__}"
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            import openai
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except ImportError:
            return "Error: 'openai' library not installed. Run: pip install openai"
        except Exception as e:
            return f"Error calling OpenAI: {e}"
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        try:
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except ImportError:
            return "Error: 'anthropic' library not installed. Run: pip install anthropic"
        except Exception as e:
            return f"Error calling Anthropic: {e}"

