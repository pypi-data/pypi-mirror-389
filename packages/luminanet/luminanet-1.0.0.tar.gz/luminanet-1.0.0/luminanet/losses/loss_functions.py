import numpy as np

class LossFunctions:
    """Comprehensive loss functions with derivatives"""
    
    @staticmethod
    def categorical_crossentropy(y_true, y_pred, epsilon=1e-15):
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))
    
    @staticmethod
    def categorical_crossentropy_derivative(y_true, y_pred, epsilon=1e-15):
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return (y_pred - y_true) / y_pred.shape[0]
    
    @staticmethod
    def binary_crossentropy(y_true, y_pred, epsilon=1e-15):
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
    
    @staticmethod
    def binary_crossentropy_derivative(y_true, y_pred, epsilon=1e-15):
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return (y_pred - y_true) / (y_pred * (1 - y_pred) * y_pred.shape[0])
    
    @staticmethod
    def mse(y_true, y_pred):
        return np.mean((y_true - y_pred) ** 2)
    
    @staticmethod
    def mse_derivative(y_true, y_pred):
        return 2 * (y_pred - y_true) / y_pred.shape[0]
    
    @staticmethod
    def mae(y_true, y_pred):
        return np.mean(np.abs(y_true - y_pred))
    
    @staticmethod
    def mae_derivative(y_true, y_pred):
        return np.sign(y_pred - y_true) / y_pred.shape[0]
    
    @staticmethod
    def huber(y_true, y_pred, delta=1.0):
        error = np.abs(y_true - y_pred)
        quadratic = np.minimum(error, delta)
        linear = error - quadratic
        return np.mean(0.5 * quadratic ** 2 + delta * linear)
    
    @staticmethod
    def huber_derivative(y_true, y_pred, delta=1.0):
        error = y_pred - y_true
        return np.where(np.abs(error) <= delta, error, delta * np.sign(error)) / y_pred.shape[0]
