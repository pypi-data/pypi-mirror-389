import numpy as np
from .activations import ActivationFunctions
from .initializers import Initializers
from .regularizers import Regularizers
from .constraints import Constraints

class Layer:
    """Base layer class with comprehensive functionality"""
    
    def __init__(self, name=None, trainable=True):
        self.name = name or self.__class__.__name__
        self.trainable = trainable
        self.params = {}
        self.grads = {}
        self.cache = {}
        self.regularizer = None
        self.constraint = None
        self.metrics = {}
        
    def build(self, input_shape):
        """Initialize layer parameters based on input shape"""
        self.input_shape = input_shape
        self.output_shape = input_shape
        
    def forward(self, x, training=True):
        """Forward pass"""
        raise NotImplementedError
        
    def backward(self, dout):
        """Backward pass"""
        raise NotImplementedError
        
    def get_params(self):
        """Get layer parameters"""
        return self.params
        
    def set_params(self, params):
        """Set layer parameters"""
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
                
    def get_config(self):
        """Get layer configuration"""
        return {
            'name': self.name,
            'trainable': self.trainable,
            'input_shape': getattr(self, 'input_shape', None),
            'output_shape': getattr(self, 'output_shape', None)
        }
        
    def count_params(self):
        """Count number of trainable parameters"""
        total = 0
        for param in self.params.values():
            total += np.prod(param.shape)
        return total
        
    def reset_metrics(self):
        """Reset layer metrics"""
        self.metrics = {}

class Dense(Layer):
    """Fully connected layer with advanced features"""
    
    def __init__(self, units, activation='relu', use_bias=True,
                 kernel_initializer='xavier_uniform',
                 bias_initializer='zeros',
                 kernel_regularizer=None,
                 bias_regularizer=None,
                 kernel_constraint=None,
                 bias_constraint=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.activation_name = activation
        self.use_bias = use_bias
        self.kernel_initializer = kernel_initializer
        self.bias_initializer = bias_initializer
        self.kernel_regularizer = kernel_regularizer
        self.bias_regularizer = bias_regularizer
        self.kernel_constraint = kernel_constraint
        self.bias_constraint = bias_constraint
        
        self.activation_fn = getattr(ActivationFunctions, activation, None)
        self.activation_derivative = getattr(ActivationFunctions, f"{activation}_derivative", None)
        
    def build(self, input_shape):
        super().build(input_shape)
        self.input_shape = input_shape
        self.output_shape = (input_shape[0], self.units)
        
        # Initialize kernel
        kernel_shape = (input_shape[1], self.units)
        if self.kernel_initializer == 'xavier_uniform':
            self.params['kernel'] = Initializers.xavier_uniform(kernel_shape)
        elif self.kernel_initializer == 'xavier_normal':
            self.params['kernel'] = Initializers.xavier_normal(kernel_shape)
        elif self.kernel_initializer == 'he_uniform':
            self.params['kernel'] = Initializers.he_uniform(kernel_shape)
        elif self.kernel_initializer == 'he_normal':
            self.params['kernel'] = Initializers.he_normal(kernel_shape)
        elif self.kernel_initializer == 'lecun_uniform':
            self.params['kernel'] = Initializers.lecun_uniform(kernel_shape)
        elif self.kernel_initializer == 'orthogonal':
            self.params['kernel'] = Initializers.orthogonal(kernel_shape)
        else:
            self.params['kernel'] = np.random.uniform(-0.05, 0.05, kernel_shape)
            
        # Initialize bias
        if self.use_bias:
            if self.bias_initializer == 'zeros':
                self.params['bias'] = np.zeros((1, self.units))
            else:
                self.params['bias'] = np.random.uniform(-0.05, 0.05, (1, self.units))
                
    def forward(self, x, training=True):
        self.cache['x'] = x
        
        # Linear transformation
        self.cache['z'] = np.dot(x, self.params['kernel'])
        if self.use_bias:
            self.cache['z'] += self.params['bias']
            
        # Activation
        if self.activation_name == 'softmax':
            self.cache['a'] = ActivationFunctions.softmax(self.cache['z'])
        elif self.activation_fn:
            self.cache['a'] = self.activation_fn(self.cache['z'])
        else:
            self.cache['a'] = self.cache['z']
            
        return self.cache['a']
    
    def backward(self, dout):
        x = self.cache['x']
        z = self.cache['z']
        batch_size = x.shape[0]
        
        # Activation derivative
        if self.activation_name == 'softmax':
            da = dout
        elif self.activation_derivative:
            da = dout * self.activation_derivative(z)
        else:
            da = dout
            
        # Compute gradients
        self.grads['kernel'] = np.dot(x.T, da) / batch_size
        if self.use_bias:
            self.grads['bias'] = np.sum(da, axis=0, keepdims=True) / batch_size
            
        # Apply regularization
        if self.kernel_regularizer == 'l1':
            self.grads['kernel'] += Regularizers.l1_gradient(self.params['kernel'])
        elif self.kernel_regularizer == 'l2':
            self.grads['kernel'] += Regularizers.l2_gradient(self.params['kernel'])
            
        if self.use_bias and self.bias_regularizer == 'l2':
            self.grads['bias'] += Regularizers.l2_gradient(self.params['bias'])
            
        # Apply constraints
        if self.kernel_constraint == 'max_norm':
            self.cache['kernel_constraint'] = lambda: Constraints.max_norm(self.params['kernel'])
        if self.use_bias and self.bias_constraint == 'max_norm':
            self.cache['bias_constraint'] = lambda: Constraints.max_norm(self.params['bias'])
            
        # Compute gradient for previous layer
        dx = np.dot(da, self.params['kernel'].T)
        return dx
    
    def apply_constraints(self):
        """Apply weight constraints after update"""
        if 'kernel_constraint' in self.cache:
            self.params['kernel'] = self.cache['kernel_constraint']()
        if 'bias_constraint' in self.cache and self.use_bias:
            self.params['bias'] = self.cache['bias_constraint']()
            
    def get_config(self):
        config = super().get_config()
        config.update({
            'units': self.units,
            'activation': self.activation_name,
            'use_bias': self.use_bias,
            'kernel_initializer': self.kernel_initializer,
            'bias_initializer': self.bias_initializer,
            'kernel_regularizer': self.kernel_regularizer,
            'bias_regularizer': self.bias_regularizer
        })
        return config

