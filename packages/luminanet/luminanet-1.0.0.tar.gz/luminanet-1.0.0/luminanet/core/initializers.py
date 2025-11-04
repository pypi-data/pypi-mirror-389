import numpy as np

class Initializers:
    """Weight initialization strategies"""
    
    @staticmethod
    def xavier_uniform(shape, gain=1.0):
        fan_in, fan_out = shape[0], shape[1] if len(shape) > 1 else shape[0]
        limit = gain * np.sqrt(6.0 / (fan_in + fan_out))
        return np.random.uniform(-limit, limit, shape)
    
    @staticmethod
    def xavier_normal(shape, gain=1.0):
        fan_in, fan_out = shape[0], shape[1] if len(shape) > 1 else shape[0]
        std = gain * np.sqrt(2.0 / (fan_in + fan_out))
        return np.random.normal(0, std, shape)
    
    @staticmethod
    def he_uniform(shape):
        fan_in = shape[0]
        limit = np.sqrt(6.0 / fan_in)
        return np.random.uniform(-limit, limit, shape)
    
    @staticmethod
    def he_normal(shape):
        fan_in = shape[0]
        std = np.sqrt(2.0 / fan_in)
        return np.random.normal(0, std, shape)
    
    @staticmethod
    def lecun_uniform(shape):
        fan_in = shape[0]
        limit = np.sqrt(3.0 / fan_in)
        return np.random.uniform(-limit, limit, shape)
    
    @staticmethod
    def orthogonal(shape, gain=1.0):
        if len(shape) < 2:
            raise ValueError("Orthogonal init requires at least 2D shape")
        
        flat_shape = (shape[0], np.prod(shape[1:]))
        a = np.random.normal(0.0, 1.0, flat_shape)
        u, _, v = np.linalg.svd(a, full_matrices=False)
        q = u if u.shape == flat_shape else v
        q = q.reshape(shape)
        return gain * q
