import numpy as np
from ..core.layers import Layer

class Dropout(Layer):
    """Dropout Layer untuk regularisasi"""
    
    def __init__(self, dropout_rate=0.5, **kwargs):
        super().__init__(**kwargs)
        self.dropout_rate = dropout_rate
        self.mask = None
    
    def forward(self, x, training=True):
        if training:
            self.mask = (np.random.random(x.shape) > self.dropout_rate)
            return x * self.mask / (1 - self.dropout_rate)
        return x
    
    def backward(self, dout):
        return dout * self.mask / (1 - self.dropout_rate)
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'dropout_rate': self.dropout_rate
        })
        return config
