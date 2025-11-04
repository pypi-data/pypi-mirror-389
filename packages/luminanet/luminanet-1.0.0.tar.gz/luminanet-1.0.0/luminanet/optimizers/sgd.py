import numpy as np
from .base import Optimizer

class SGD(Optimizer):
    """Stochastic Gradient Descent with momentum"""
    
    def __init__(self, learning_rate=0.01, momentum=0.0, nesterov=False, **kwargs):
        super().__init__(learning_rate, **kwargs)
        self.momentum = momentum
        self.nesterov = nesterov
        self.velocities = {}
        
    def apply_gradients(self, grads, params, layer_id):
        if layer_id not in self.velocities:
            self.velocities[layer_id] = {
                key: np.zeros_like(value) for key, value in params.items()
            }
            
        grads = self._clip_gradients(grads)
        
        for key in params.keys():
            velocity = self.velocities[layer_id][key]
            velocity = self.momentum * velocity - self.learning_rate * grads[key]
            self.velocities[layer_id][key] = velocity
            
            if self.nesterov:
                params[key] += self.momentum * velocity - self.learning_rate * grads[key]
            else:
                params[key] += velocity
                
        self.iterations += 1
