import numpy as np
from ..core.layers import Layer
from ..core.activations import ActivationFunctions
from ..core.initializers import Initializers

class Conv2D(Layer):
    """2D Convolutional Layer dengan numpy murni"""
    
    def __init__(self, filters, kernel_size, strides=(1, 1), padding='same',
                 activation='relu', use_bias=True, **kwargs):
        super().__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size if isinstance(kernel_size, tuple) else (kernel_size, kernel_size)
        self.strides = strides if isinstance(strides, tuple) else (strides, strides)
        self.padding = padding
        self.activation_name = activation
        self.use_bias = use_bias
        
        self.activation_fn = getattr(ActivationFunctions, activation, None)
        self.activation_derivative = getattr(ActivationFunctions, f"{activation}_derivative", None)
        
    def build(self, input_shape):
        super().build(input_shape)
        batch_size, input_height, input_width, input_channels = input_shape
        
        # Initialize kernels
        kernel_shape = (*self.kernel_size, input_channels, self.filters)
        self.params['kernel'] = Initializers.he_normal(kernel_shape)
        
        if self.use_bias:
            self.params['bias'] = np.zeros((1, 1, 1, self.filters))
            
        # Calculate output shape
        if self.padding == 'same':
            output_height = int(np.ceil(input_height / self.strides[0]))
            output_width = int(np.ceil(input_width / self.strides[1]))
        else:  # valid
            output_height = int(np.ceil((input_height - self.kernel_size[0] + 1) / self.strides[0]))
            output_width = int(np.ceil((input_width - self.kernel_size[1] + 1) / self.strides[1]))
            
        self.output_shape = (batch_size, output_height, output_width, self.filters)
        
    def _pad_input(self, x):
        """Apply padding to input"""
        if self.padding == 'same':
            pad_h = int(((self.output_shape[1] - 1) * self.strides[0] + 
                        self.kernel_size[0] - self.input_shape[1]) / 2)
            pad_w = int(((self.output_shape[2] - 1) * self.strides[1] + 
                        self.kernel_size[1] - self.input_shape[2]) / 2)
            x_padded = np.pad(x, ((0, 0), (pad_h, pad_h), (pad_w, pad_w), (0, 0)), 
                            mode='constant')
        else:  # valid
            x_padded = x
        return x_padded
        
    def forward(self, x, training=True):
        self.cache['x'] = x
        x_padded = self._pad_input(x)
        
        batch_size, input_height, input_width, input_channels = x_padded.shape
        output_height, output_width = self.output_shape[1], self.output_shape[2]
        
        # Initialize output
        output = np.zeros((batch_size, output_height, output_width, self.filters))
        
        # Perform convolution
        for i in range(output_height):
            for j in range(output_width):
                h_start = i * self.strides[0]
                h_end = h_start + self.kernel_size[0]
                w_start = j * self.strides[1]
                w_end = w_start + self.kernel_size[1]
                
                x_slice = x_padded[:, h_start:h_end, w_start:w_end, :]
                output[:, i, j, :] = np.tensordot(x_slice, self.params['kernel'], axes=([1,2,3], [0,1,2]))
                
        if self.use_bias:
            output += self.params['bias']
            
        self.cache['z'] = output
        
        # Apply activation
        if self.activation_name == 'softmax':
            output = ActivationFunctions.softmax(output.reshape(batch_size, -1))
            output = output.reshape(batch_size, output_height, output_width, self.filters)
        elif self.activation_fn:
            output = self.activation_fn(output)
            
        self.cache['a'] = output
        return output
    
    def backward(self, dout):
        x = self.cache['x']
        x_padded = self._pad_input(x)
        batch_size = x.shape[0]
        
        # Activation derivative
        if self.activation_derivative:
            dout = dout * self.activation_derivative(self.cache['z'])
            
        # Initialize gradients
        self.grads['kernel'] = np.zeros_like(self.params['kernel'])
        if self.use_bias:
            self.grads['bias'] = np.zeros_like(self.params['bias'])
            
        dx_padded = np.zeros_like(x_padded)
        
        output_height, output_width = self.output_shape[1], self.output_shape[2]
        
        # Compute gradients
        for i in range(output_height):
            for j in range(output_width):
                h_start = i * self.strides[0]
                h_end = h_start + self.kernel_size[0]
                w_start = j * self.strides[1]
                w_end = w_start + self.kernel_size[1]
                
                x_slice = x_padded[:, h_start:h_end, w_start:w_end, :]
                
                # Kernel gradient
                for f in range(self.filters):
                    self.grads['kernel'][:, :, :, f] += np.tensordot(
                        x_slice, dout[:, i, j, f], axes=([0], [0])
                    )
                
                # Input gradient
                dx_padded[:, h_start:h_end, w_start:w_end, :] += np.tensordot(
                    dout[:, i, j, :], self.params['kernel'], axes=([1], [3])
                )
                
        # Average gradients
        self.grads['kernel'] /= batch_size
        if self.use_bias:
            self.grads['bias'] = np.sum(dout, axis=(0, 1, 2), keepdims=True) / batch_size
            
        # Remove padding from input gradient
        if self.padding == 'same':
            pad_h = (x_padded.shape[1] - x.shape[1]) // 2
            pad_w = (x_padded.shape[2] - x.shape[2]) // 2
            dx = dx_padded[:, pad_h:pad_h+x.shape[1], pad_w:pad_w+x.shape[2], :]
        else:
            dx = dx_padded
            
        return dx

class MaxPooling2D(Layer):
    """2D Max Pooling Layer"""
    
    def __init__(self, pool_size=(2, 2), strides=None, padding='valid', **kwargs):
        super().__init__(**kwargs)
        self.pool_size = pool_size if isinstance(pool_size, tuple) else (pool_size, pool_size)
        self.strides = strides if strides else pool_size
        self.strides = self.strides if isinstance(self.strides, tuple) else (self.strides, self.strides)
        self.padding = padding
        
    def build(self, input_shape):
        super().build(input_shape)
        batch_size, input_height, input_width, input_channels = input_shape
        
        # Calculate output shape
        if self.padding == 'same':
            output_height = int(np.ceil(input_height / self.strides[0]))
            output_width = int(np.ceil(input_width / self.strides[1]))
        else:  # valid
            output_height = int((input_height - self.pool_size[0]) / self.strides[0] + 1)
            output_width = int((input_width - self.pool_size[1]) / self.strides[1] + 1)
            
        self.output_shape = (batch_size, output_height, output_width, input_channels)
        
    def forward(self, x, training=True):
        self.cache['x'] = x
        
        batch_size, input_height, input_width, input_channels = x.shape
        output_height, output_width = self.output_shape[1], self.output_shape[2]
        
        output = np.zeros(self.output_shape)
        self.cache['max_mask'] = np.zeros_like(x)
        
        for i in range(output_height):
            for j in range(output_width):
                h_start = i * self.strides[0]
                h_end = h_start + self.pool_size[0]
                w_start = j * self.strides[1]
                w_end = w_start + self.pool_size[1]
                
                x_slice = x[:, h_start:h_end, w_start:w_end, :]
                output[:, i, j, :] = np.max(x_slice, axis=(1, 2))
                
                # Create mask for max values
                max_vals = output[:, i, j, :][:, None, None, :]
                mask = (x_slice == max_vals)
                self.cache['max_mask'][:, h_start:h_end, w_start:w_end, :] += mask
                
        return output
    
    def backward(self, dout):
        x = self.cache['x']
        batch_size, input_height, input_width, input_channels = x.shape
        output_height, output_width = self.output_shape[1], self.output_shape[2]
        
        dx = np.zeros_like(x)
        
        for i in range(output_height):
            for j in range(output_width):
                h_start = i * self.strides[0]
                h_end = h_start + self.pool_size[0]
                w_start = j * self.strides[1]
                w_end = w_start + self.pool_size[1]
                
                # Distribute gradient to max positions
                mask_slice = self.cache['max_mask'][:, h_start:h_end, w_start:w_end, :]
                dout_slice = dout[:, i, j, :][:, None, None, :]
                dx[:, h_start:h_end, w_start:w_end, :] += mask_slice * dout_slice
                
        return dx
