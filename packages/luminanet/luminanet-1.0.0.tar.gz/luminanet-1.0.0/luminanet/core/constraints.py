import numpy as np

class Constraints:
    """Weight constraints"""
    
    @staticmethod
    def max_norm(weights, max_value=2.0, axis=0):
        norms = np.sqrt(np.sum(weights ** 2, axis=axis, keepdims=True))
        desired = np.clip(norms, 0, max_value)
        weights = weights * (desired / (norms + 1e-7))
        return weights
    
    @staticmethod
    def unit_norm(weights, axis=0):
        norms = np.sqrt(np.sum(weights ** 2, axis=axis, keepdims=True))
        return weights / (norms + 1e-7)
    
    @staticmethod
    def non_neg(weights):
        return np.maximum(weights, 0)
    
    @staticmethod
    def min_max_norm(weights, min_value=0.0, max_value=1.0):
        return np.clip(weights, min_value, max_value)
