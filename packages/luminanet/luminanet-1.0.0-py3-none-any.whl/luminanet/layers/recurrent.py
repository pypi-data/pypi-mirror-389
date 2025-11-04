import numpy as np
from ..core.layers import Layer
from ..core.activations import ActivationFunctions
from ..core.initializers import Initializers

class LSTM(Layer):
    """Long Short-Term Memory Layer"""
    
    def __init__(self, units, return_sequences=False, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.return_sequences = return_sequences
        
    def build(self, input_shape):
        super().build(input_shape)
        batch_size, timesteps, input_dim = input_shape
        
        # Input weights
        self.params['W_i'] = Initializers.orthogonal((input_dim, self.units))
        self.params['U_i'] = Initializers.orthogonal((self.units, self.units))
        self.params['b_i'] = np.zeros((1, self.units))
        
        # Forget weights
        self.params['W_f'] = Initializers.orthogonal((input_dim, self.units))
        self.params['U_f'] = Initializers.orthogonal((self.units, self.units))
        self.params['b_f'] = np.ones((1, self.units))
        
        # Cell weights
        self.params['W_c'] = Initializers.orthogonal((input_dim, self.units))
        self.params['U_c'] = Initializers.orthogonal((self.units, self.units))
        self.params['b_c'] = np.zeros((1, self.units))
        
        # Output weights
        self.params['W_o'] = Initializers.orthogonal((input_dim, self.units))
        self.params['U_o'] = Initializers.orthogonal((self.units, self.units))
        self.params['b_o'] = np.zeros((1, self.units))
        
        if self.return_sequences:
            self.output_shape = (batch_size, timesteps, self.units)
        else:
            self.output_shape = (batch_size, self.units)
            
    def forward(self, x, training=True):
        batch_size, timesteps, input_dim = x.shape
        
        # Initialize states
        h_t = np.zeros((batch_size, self.units))
        c_t = np.zeros((batch_size, self.units))
        
        self.cache['x'] = x
        self.cache['h'] = np.zeros((batch_size, timesteps, self.units))
        self.cache['c'] = np.zeros((batch_size, timesteps, self.units))
        self.cache['gate_i'] = np.zeros((batch_size, timesteps, self.units))
        self.cache['gate_f'] = np.zeros((batch_size, timesteps, self.units))
        self.cache['gate_c'] = np.zeros((batch_size, timesteps, self.units))
        self.cache['gate_o'] = np.zeros((batch_size, timesteps, self.units))
        
        # Process each timestep
        for t in range(timesteps):
            x_t = x[:, t, :]
            
            # Input gate
            i_t = ActivationFunctions.sigmoid(
                np.dot(x_t, self.params['W_i']) + 
                np.dot(h_t, self.params['U_i']) + 
                self.params['b_i']
            )
            
            # Forget gate
            f_t = ActivationFunctions.sigmoid(
                np.dot(x_t, self.params['W_f']) + 
                np.dot(h_t, self.params['U_f']) + 
                self.params['b_f']
            )
            
            # Cell candidate
            c_hat_t = ActivationFunctions.tanh(
                np.dot(x_t, self.params['W_c']) + 
                np.dot(h_t, self.params['U_c']) + 
                self.params['b_c']
            )
            
            # Update cell state
            c_t = f_t * c_t + i_t * c_hat_t
            
            # Output gate
            o_t = ActivationFunctions.sigmoid(
                np.dot(x_t, self.params['W_o']) + 
                np.dot(h_t, self.params['U_o']) + 
                self.params['b_o']
            )
            
            # Update hidden state
            h_t = o_t * ActivationFunctions.tanh(c_t)
            
            # Store for backward pass
            self.cache['h'][:, t, :] = h_t
            self.cache['c'][:, t, :] = c_t
            self.cache['gate_i'][:, t, :] = i_t
            self.cache['gate_f'][:, t, :] = f_t
            self.cache['gate_c'][:, t, :] = c_hat_t
            self.cache['gate_o'][:, t, :] = o_t
            
        if self.return_sequences:
            return self.cache['h']
        else:
            return h_t.reshape(batch_size, self.units)
    
    def backward(self, dout):
        x = self.cache['x']
        batch_size, timesteps, input_dim = x.shape
        
        if not self.return_sequences:
            dout_seq = np.zeros((batch_size, timesteps, self.units))
            dout_seq[:, -1, :] = dout
            dout = dout_seq
        
        # Initialize gradients
        grads = {key: np.zeros_like(value) for key, value in self.params.items()}
        dx = np.zeros_like(x)
        
        # Initialize state gradients
        dh_next = np.zeros((batch_size, self.units))
        dc_next = np.zeros((batch_size, self.units))
        
        # Backward through time
        for t in reversed(range(timesteps)):
            # Get cached values
            h_t = self.cache['h'][:, t, :]
            h_prev = self.cache['h'][:, t-1, :] if t > 0 else np.zeros((batch_size, self.units))
            c_prev = self.cache['c'][:, t-1, :] if t > 0 else np.zeros((batch_size, self.units))
            c_t = self.cache['c'][:, t, :]
            i_t = self.cache['gate_i'][:, t, :]
            f_t = self.cache['gate_f'][:, t, :]
            c_hat_t = self.cache['gate_c'][:, t, :]
            o_t = self.cache['gate_o'][:, t, :]
            x_t = x[:, t, :]
            
            # Combine gradients
            dh = dout[:, t, :] + dh_next
            dc = dc_next + (dh * o_t * (1 - ActivationFunctions.tanh(c_t) ** 2))
            
            # Gate gradients
            do = dh * ActivationFunctions.tanh(c_t) * o_t * (1 - o_t)
            dc_hat = dc * i_t * (1 - c_hat_t ** 2)
            di = dc * c_hat_t * i_t * (1 - i_t)
            df = dc * c_prev * f_t * (1 - f_t)
            
            # Parameter gradients
            grads['W_o'] += np.dot(x_t.T, do)
            grads['U_o'] += np.dot(h_prev.T, do)
            grads['b_o'] += np.sum(do, axis=0, keepdims=True)
            
            grads['W_c'] += np.dot(x_t.T, dc_hat)
            grads['U_c'] += np.dot(h_prev.T, dc_hat)
            grads['b_c'] += np.sum(dc_hat, axis=0, keepdims=True)
            
            grads['W_i'] += np.dot(x_t.T, di)
            grads['U_i'] += np.dot(h_prev.T, di)
            grads['b_i'] += np.sum(di, axis=0, keepdims=True)
            
            grads['W_f'] += np.dot(x_t.T, df)
            grads['U_f'] += np.dot(h_prev.T, df)
            grads['b_f'] += np.sum(df, axis=0, keepdims=True)
            
            # Input gradient
            dx[:, t, :] = (np.dot(do, self.params['W_o'].T) +
                          np.dot(dc_hat, self.params['W_c'].T) +
                          np.dot(di, self.params['W_i'].T) +
                          np.dot(df, self.params['W_f'].T))
            
            # State gradients for next timestep
            dh_next = (np.dot(do, self.params['U_o'].T) +
                      np.dot(dc_hat, self.params['U_c'].T) +
                      np.dot(di, self.params['U_i'].T) +
                      np.dot(df, self.params['U_f'].T))
            dc_next = dc * f_t
            
        # Average gradients
        for key in grads:
            grads[key] /= batch_size
            
        self.grads.update(grads)
        return dx
