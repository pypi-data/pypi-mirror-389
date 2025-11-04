import numpy as np
from .base import Optimizer

class Adam(Optimizer):
    """Adam optimizer"""
    
    def __init__(self, learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-7, **kwargs):
        super().__init__(learning_rate, **kwargs)
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.m = {}
        self.v = {}
        
    def apply_gradients(self, grads, params, layer_id):
        if layer_id not in self.m:
            self.m[layer_id] = {key: np.zeros_like(value) for key, value in params.items()}
            self.v[layer_id] = {key: np.zeros_like(value) for key, value in params.items()}
            
        grads = self._clip_gradients(grads)
        self.iterations += 1
        
        t = self.iterations
        lr_t = self.learning_rate * np.sqrt(1 - self.beta2**t) / (1 - self.beta1**t)
        
        for key in params.keys():
            # Update biased first moment estimate
            self.m[layer_id][key] = self.beta1 * self.m[layer_id][key] + (1 - self.beta1) * grads[key]
            
            # Update biased second raw moment estimate
            self.v[layer_id][key] = self.beta2 * self.v[layer_id][key] + (1 - self.beta2) * (grads[key]**2)
            
            # Compute bias-corrected first moment estimate
            m_hat = self.m[layer_id][key] / (1 - self.beta1**t)
            
            # Compute bias-corrected second raw moment estimate
            v_hat = self.v[layer_id][key] / (1 - self.beta2**t)
            
            # Update parameters
            params[key] -= lr_t * m_hat / (np.sqrt(v_hat) + self.epsilon)
