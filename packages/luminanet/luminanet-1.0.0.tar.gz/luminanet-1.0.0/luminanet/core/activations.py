import numpy as np
import scipy.special

class ActivationFunctions:
    """Comprehensive activation functions with derivatives"""
    
    @staticmethod
    def sigmoid(x):
        return scipy.special.expit(x)
    
    @staticmethod
    def sigmoid_derivative(x):
        s = scipy.special.expit(x)
        return s * (1 - s)
    
    @staticmethod
    def tanh(x):
        return np.tanh(x)
    
    @staticmethod
    def tanh_derivative(x):
        return 1 - np.tanh(x) ** 2
    
    @staticmethod
    def relu(x):
        return np.maximum(0, x)
    
    @staticmethod
    def relu_derivative(x):
        return (x > 0).astype(float)
    
    @staticmethod
    def leaky_relu(x, alpha=0.01):
        return np.where(x > 0, x, x * alpha)
    
    @staticmethod
    def leaky_relu_derivative(x, alpha=0.01):
        return np.where(x > 0, 1, alpha)
    
    @staticmethod
    def elu(x, alpha=1.0):
        return np.where(x > 0, x, alpha * (np.exp(x) - 1))
    
    @staticmethod
    def elu_derivative(x, alpha=1.0):
        return np.where(x > 0, 1, alpha * np.exp(x))
    
    @staticmethod
    def softmax(x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    @staticmethod
    def softmax_derivative(x):
        return x * (1 - x)
    
    @staticmethod
    def swish(x, beta=1.0):
        return x * scipy.special.expit(beta * x)
    
    @staticmethod
    def swish_derivative(x, beta=1.0):
        sigmoid = scipy.special.expit(beta * x)
        return sigmoid + beta * x * sigmoid * (1 - sigmoid)
    
    @staticmethod
    def gelu(x):
        return 0.5 * x * (1 + scipy.special.erf(x / np.sqrt(2)))
    
    @staticmethod
    def gelu_derivative(x):
        return 0.5 * (1 + scipy.special.erf(x / np.sqrt(2))) + \
               (x * np.exp(-x**2 / 2)) / (np.sqrt(2 * np.pi))
