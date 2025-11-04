import numpy as np
from .base import Optimizer

class RMSprop(Optimizer):
    """RMSprop optimizer"""
    
    def __init__(self, learning_rate=0.001, rho=0.9, epsilon=1e-7, **kwargs):
        super().__init__(learning_rate, **kwargs)
        self.rho = rho
        self.epsilon = epsilon
        self.accumulators = {}
        
    def apply_gradients(self, grads, params, layer_id):
        if layer_id not in self.accumulators:
            self.accumulators[layer_id] = {
                key: np.zeros_like(value) for key, value in params.items()
            }
            
        grads = self._clip_gradients(grads)
        
        for key in params.keys():
            # Update accumulator
            self.accumulators[layer_id][key] = (
                self.rho * self.accumulators[layer_id][key] + 
                (1 - self.rho) * grads[key]**2
            )
            
            # Update parameters
            params[key] -= (
                self.learning_rate * grads[key] / 
                (np.sqrt(self.accumulators[layer_id][key]) + self.epsilon)
            )
            
        self.iterations += 1
