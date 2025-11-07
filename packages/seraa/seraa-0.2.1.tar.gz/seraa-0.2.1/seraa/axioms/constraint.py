"""
seraa/axioms/constraint.py - Axiom 6: Ethical Constraint (Exclusion Principle)

Defines non-negotiable ethical boundaries that cannot be violated.
Like the Pauli exclusion principle, certain ethical states cannot coexist.
"""

from typing import Dict, List, Callable, Any, Optional
from ..core.ternary import TernaryValue, TernaryState


class EthicalConstraint:
    """
    Represents a hard constraint on ethical behavior.
    
    Example:
        >>> def no_harm(action):
        ...     return action.get('harm_level', 0) == 0
        >>> 
        >>> constraint = EthicalConstraint(
        ...     name="non_maleficence",
        ...     checker=no_harm,
        ...     violation_message="Action causes harm"
        ... )
        >>> result = constraint.evaluate({'harm_level': 0})
        >>> print(result.is_violated())
        False
    """
    
    def __init__(
        self,
        name: str,
        checker: Callable[[Any], bool],
        violation_message: str = "Constraint violated"
    ):
        """
        Args:
            name: Identifier for this constraint
            checker: Function that returns True if constraint is satisfied
            violation_message: Message when constraint is violated
        """
        self.name = name
        self.checker = checker
        self.violation_message = violation_message
    
    def evaluate(self, action: Any) -> 'ConstraintResult':
        """
        Evaluate if action satisfies constraint.
        
        Args:
            action: Action to evaluate
            
        Returns:
            ConstraintResult indicating satisfaction or violation
        """
        satisfied = self.checker(action)
        
        if satisfied:
            state = TernaryValue(TernaryState.NEUTRAL)  # Constraint satisfied
        else:
            state = TernaryValue(TernaryState.NEGATIVE)  # Violation
        
        return ConstraintResult(
            constraint_name=self.name,
            satisfied=satisfied,
            state=state,
            message=self.violation_message if not satisfied else "Constraint satisfied"
        )


class ConstraintResult:
    """Result of constraint evaluation."""
    
    def __init__(
        self,
        constraint_name: str,
        satisfied: bool,
        state: TernaryValue,
        message: str
    ):
        self.constraint_name = constraint_name
        self.satisfied = satisfied
        self.state = state
        self.message = message
    
    def is_violated(self) -> bool:
        """Returns True if constraint was violated."""
        return not self.satisfied
    
    def __repr__(self):
        status = "✓ Satisfied" if self.satisfied else "✗ Violated"
        return f"ConstraintResult({self.constraint_name}: {status})"


class ConstraintSystem:
    """
    Manages multiple ethical constraints for a system.
    
    Example:
        >>> system = ConstraintSystem()
        >>> system.add_constraint(EthicalConstraint("no_harm", lambda a: a['harm'] == 0))
        >>> system.add_constraint(EthicalConstraint("consent", lambda a: a['has_consent']))
        >>> results = system.evaluate_all({'harm': 0, 'has_consent': True})
        >>> print(system.all_satisfied(results))
        True
    """
    
    def __init__(self):
        self.constraints: List[EthicalConstraint] = []
    
    def add_constraint(self, constraint: EthicalConstraint) -> None:
        """Add a constraint to the system."""
        self.constraints.append(constraint)
    
    def evaluate_all(self, action: Any) -> List[ConstraintResult]:
        """
        Evaluate action against all constraints.
        
        Args:
            action: Action to evaluate
            
        Returns:
            List of ConstraintResults
        """
        return [constraint.evaluate(action) for constraint in self.constraints]
    
    def all_satisfied(self, results: Optional[List[ConstraintResult]] = None, action: Any = None) -> bool:
        """
        Check if all constraints are satisfied.
        
        Args:
            results: Pre-computed results, or None to evaluate action
            action: Action to evaluate if results not provided
            
        Returns:
            True if all constraints satisfied
        """
        if results is None:
            if action is None:
                raise ValueError("Must provide either results or action")
            results = self.evaluate_all(action)
        
        return all(result.satisfied for result in results)
    
    def get_violations(self, action: Any) -> List[ConstraintResult]:
        """
        Get list of violated constraints.
        
        Args:
            action: Action to evaluate
            
        Returns:
            List of violated ConstraintResults
        """
        results = self.evaluate_all(action)
        return [r for r in results if r.is_violated()]


# Common constraint templates
def create_threshold_constraint(
    name: str,
    attribute: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> EthicalConstraint:
    """
    Create a constraint that checks if attribute is within bounds.
    
    Args:
        name: Constraint name
        attribute: Attribute to check
        min_value: Minimum acceptable value (or None)
        max_value: Maximum acceptable value (or None)
        
    Returns:
        EthicalConstraint
    """
    def checker(action):
        value = action.get(attribute, 0)
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        return True
    
    return EthicalConstraint(
        name=name,
        checker=checker,
        violation_message=f"{attribute} outside acceptable range"
    )
