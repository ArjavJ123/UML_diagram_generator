"""
Generic decorators for retry logic and error handling
"""
import functools
from typing import Callable, Any, Optional


def retry_on_failure(max_retries: int = 3, validation_method: Optional[str] = None):
    """
    Generic retry decorator for any method that might fail
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        validation_method: Optional name of validation method to call after execution
                          Method should return (bool, str) where bool is success and str is error message
    
    Usage:
        @retry_on_failure(max_retries=3, validation_method='validate_output')
        def execute(self, state):
            # method implementation
            
        def validate_output(self, state):
            # validation logic
            return (True, "") if valid else (False, "error message")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, state, *args, **kwargs):
            last_error = None
            last_validation_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"[{self.name}] Attempt {attempt}/{max_retries}")
                    
                    # Call the original method
                    result_state = func(self, state, *args, **kwargs)
                    
                    # If validation method specified, call it
                    if validation_method:
                        if hasattr(self, validation_method):
                            validator = getattr(self, validation_method)
                            is_valid, error_msg = validator(result_state)
                            
                            if is_valid:
                                print(f"[{self.name}] ✓ Validation passed on attempt {attempt}")
                                return result_state
                            else:
                                last_validation_error = error_msg
                                raise ValueError(f"Validation failed: {error_msg}")
                        else:
                            print(f"[{self.name}] Warning: Validation method '{validation_method}' not found")
                            return result_state
                    else:
                        # No validation needed, return result
                        print(f"[{self.name}] ✓ Execution completed on attempt {attempt}")
                        return result_state
                
                except Exception as e:
                    last_error = e
                    print(f"[{self.name}] ✗ Attempt {attempt} failed: {type(e).__name__}: {e}")
                    
                    if attempt < max_retries:
                        print(f"[{self.name}] Retrying...")
                    else:
                        print(f"[{self.name}] All {max_retries} attempts exhausted")
            
            # All retries exhausted
            error_details = f"Last error: {last_error}"
            if last_validation_error:
                error_details += f" | Validation error: {last_validation_error}"
            
            raise RuntimeError(
                f"[{self.name}] Failed after {max_retries} attempts. {error_details}"
            )
        
        return wrapper
    return decorator