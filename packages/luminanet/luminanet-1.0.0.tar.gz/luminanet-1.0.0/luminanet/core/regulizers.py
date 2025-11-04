import numpy as np

class Regularizers:
    """Regularization techniques"""
    
    @staticmethod
    def l1_regularization(weights, lambda_=0.01):
        return lambda_ * np.sum(np.abs(weights))
    
    @staticmethod
    def l1_gradient(weights, lambda_=0.01):
        return lambda_ * np.sign(weights)
    
    @staticmethod
    def l2_regularization(weights, lambda_=0.01):
        return 0.5 * lambda_ * np.sum(weights ** 2)
    
    @staticmethod
    def l2_gradient(weights, lambda_=0.01):
        return lambda_ * weights
    
    @staticmethod
    def elastic_net_regularization(weights, l1_ratio=0.5, lambda_=0.01):
        l1_term = l1_ratio * Regularizers.l1_regularization(weights, 1.0)
        l2_term = (1 - l1_ratio) * Regularizers.l2_regularization(weights, 1.0)
        return lambda_ * (l1_term + l2_term)
    
    @staticmethod
    def elastic_net_gradient(weights, l1_ratio=0.5, lambda_=0.01):
        l1_grad = l1_ratio * Regularizers.l1_gradient(weights, 1.0)
        l2_grad = (1 - l1_ratio) * Regularizers.l2_gradient(weights, 1.0)
        return lambda_ * (l1_grad + l2_grad)
