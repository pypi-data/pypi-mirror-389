import numpy as np
import time
import json
from ..optimizers.sgd import SGD
from ..optimizers.adam import Adam
from ..optimizers.rmsprop import RMSprop
from ..losses.loss_functions import LossFunctions

class NeuralNetwork:
    """Comprehensive Neural Network Model"""
    
    def __init__(self, name="model"):
        self.name = name
        self.layers = []
        self.optimizer = None
        self.loss_fn = None
        self.loss_derivative = None
        self.loss_history = []
        self.val_loss_history = []
        self.metrics_history = []
        self.best_weights = None
        self.early_stopping = None
        
    def add(self, layer):
        self.layers.append(layer)
        
    def compile(self, optimizer='adam', learning_rate=0.001, loss='categorical_crossentropy', metrics=None):
        # Initialize optimizer
        if optimizer == 'adam':
            self.optimizer = Adam(learning_rate=learning_rate)
        elif optimizer == 'sgd':
            self.optimizer = SGD(learning_rate=learning_rate)
        elif optimizer == 'rmsprop':
            self.optimizer = RMSprop(learning_rate=learning_rate)
        elif isinstance(optimizer, Optimizer):
            self.optimizer = optimizer
        else:
            self.optimizer = SGD(learning_rate=learning_rate)
            
        # Initialize loss function
        self.loss_fn = getattr(LossFunctions, loss)
        self.loss_derivative = getattr(LossFunctions, f"{loss}_derivative", None)
        
        self.metrics = metrics or []
        
        # Build layers
        input_shape = None
        for layer in self.layers:
            if input_shape is None:
                # First layer needs input shape
                continue
            layer.build(input_shape)
            input_shape = layer.output_shape
            
    def summary(self):
        """Print model summary"""
        print(f"Model: {self.name}")
        print("=" * 60)
        print(f"{'Layer (type)':<20} {'Output Shape':<20} {'Param #':<10}")
        print("=" * 60)
        
        total_params = 0
        for i, layer in enumerate(self.layers):
            layer_name = f"{layer.name} ({layer.__class__.__name__})"
            output_shape = str(layer.output_shape) if hasattr(layer, 'output_shape') else "Multiple"
            params = layer.count_params() if hasattr(layer, 'count_params') else 0
            total_params += params
            
            print(f"{layer_name:<20} {output_shape:<20} {params:<10}")
            
        print("=" * 60)
        print(f"Total params: {total_params}")
        print("=" * 60)
        
    def train(self, X, y, epochs=100, batch_size=32, validation_data=None, 
              verbose=True, callbacks=None, shuffle=True):
        
        callbacks = callbacks or []
        n_samples = X.shape[0]
        
        for epoch in range(epochs):
            epoch_start = time.time()
            
            if shuffle:
                indices = np.random.permutation(n_samples)
                X_shuffled = X[indices]
                y_shuffled = y[indices]
            else:
                X_shuffled = X
                y_shuffled = y
                
            epoch_loss = 0
            batches_per_epoch = (n_samples - 1) // batch_size + 1
            
            for batch in range(batches_per_epoch):
                start = batch * batch_size
                end = min(start + batch_size, n_samples)
                
                X_batch = X_shuffled[start:end]
                y_batch = y_shuffled[start:end]
                
                # Forward pass
                y_pred = self.forward(X_batch, training=True)
                
                # Compute loss
                batch_loss = self.loss_fn(y_batch, y_pred)
                epoch_loss += batch_loss
                
                # Backward pass
                dout = self.loss_derivative(y_batch, y_pred)
                self.backward(dout)
                
                # Update weights
                self.update_weights()
                
            # Average epoch loss
            epoch_loss /= batches_per_epoch
            self.loss_history.append(epoch_loss)
            
            # Validation
            val_loss = None
            val_metrics = None
            if validation_data:
                val_loss, val_metrics = self.evaluate(validation_data[0], validation_data[1], verbose=False)
                self.val_loss_history.append(val_loss)
                
            # Metrics
            epoch_metrics = self._compute_metrics(X, y)
            self.metrics_history.append(epoch_metrics)
            
            epoch_time = time.time() - epoch_start
            
            # Print progress
            if verbose and epoch % 10 == 0:
                self._print_epoch_progress(epoch, epochs, epoch_loss, val_loss, epoch_metrics, epoch_time)
                
            # Callbacks
            for callback in callbacks:
                callback.on_epoch_end(epoch, {
                    'loss': epoch_loss,
                    'val_loss': val_loss,
                    'metrics': epoch_metrics
                })
                
            # Early stopping check
            if self.early_stopping and self._check_early_stopping():
                if verbose:
                    print(f"Early stopping at epoch {epoch}")
                break
                
    def forward(self, X, training=True):
        """Forward pass through all layers"""
        output = X
        for layer in self.layers:
            output = layer.forward(output, training=training)
        return output
    
    def backward(self, dout):
        """Backward pass through all layers"""
        for layer in reversed(self.layers):
            dout = layer.backward(dout)
        return dout
    
    def update_weights(self):
        """Update weights using optimizer"""
        for i, layer in enumerate(self.layers):
            if layer.trainable and hasattr(layer, 'params') and layer.params:
                self.optimizer.apply_gradients(layer.grads, layer.params, i)
                
                # Apply constraints
                if hasattr(layer, 'apply_constraints'):
                    layer.apply_constraints()
                    
    def predict(self, X):
        """Make predictions"""
        return self.forward(X, training=False)
    
    def predict_classes(self, X):
        """Predict class labels"""
        proba = self.predict(X)
        return np.argmax(proba, axis=1)
    
    def evaluate(self, X, y, verbose=True):
        """Evaluate model on test data"""
        y_pred = self.predict(X)
        loss = self.loss_fn(y, y_pred)
        
        metrics = self._compute_metrics(X, y)
        
        if verbose:
            print(f"Test loss: {loss:.4f}")
            for metric_name, metric_value in metrics.items():
                print(f"Test {metric_name}: {metric_value:.4f}")
                
        return loss, metrics
    
    def _compute_metrics(self, X, y):
        """Compute evaluation metrics"""
        metrics = {}
        y_pred = self.predict(X)
        
        if 'accuracy' in self.metrics:
            if len(y.shape) > 1 and y.shape[1] > 1:
                # Multi-class classification
                y_true_classes = np.argmax(y, axis=1)
                y_pred_classes = np.argmax(y_pred, axis=1)
                accuracy = np.mean(y_true_classes == y_pred_classes)
            else:
                # Binary classification
                y_pred_binary = (y_pred > 0.5).astype(int)
                accuracy = np.mean(y.flatten() == y_pred_binary.flatten())
            metrics['accuracy'] = accuracy
            
        return metrics
    
    def _print_epoch_progress(self, epoch, epochs, loss, val_loss, metrics, epoch_time):
        """Print training progress for an epoch"""
        line = f"Epoch {epoch}/{epochs} - {epoch_time:.2f}s - loss: {loss:.4f}"
        if val_loss is not None:
            line += f" - val_loss: {val_loss:.4f}"
        for metric_name, metric_value in metrics.items():
            line += f" - {metric_name}: {metric_value:.4f}"
        print(line)
    
    def _check_early_stopping(self):
        """Check if early stopping condition is met"""
        if len(self.val_loss_history) < self.early_stopping['patience'] + 1:
            return False
            
        min_val_loss = min(self.val_loss_history)
        current_val_loss = self.val_loss_history[-1]
        
        if current_val_loss > min_val_loss + self.early_stopping['min_delta']:
            self.early_stopping['wait'] += 1
            if self.early_stopping['wait'] >= self.early_stopping['patience']:
                return True
        else:
            self.early_stopping['wait'] = 0
            
        return False
    
    def save(self, filepath):
        """Save model to file"""
        model_data = {
            'name': self.name,
            'layers': [],
            'loss_history': self.loss_history,
            'val_loss_history': self.val_loss_history,
            'metrics_history': self.metrics_history
        }
        
        for layer in self.layers:
            layer_data = {
                'type': type(layer).__name__,
                'config': layer.get_config(),
                'params': {k: v.tolist() for k, v in layer.params.items()} if hasattr(layer, 'params') else {}
            }
            model_data['layers'].append(layer_data)
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
    
    def load(self, filepath):
        """Load model from file"""
        with open(filepath, 'r') as f:
            model_data = json.load(f)
            
        self.name = model_data['name']
        self.loss_history = model_data['loss_history']
        self.val_loss_history = model_data['val_loss_history']
        self.metrics_history = model_data['metrics_history']
        
        self.layers = []
        for layer_data in model_data['layers']:
            layer_type = globals()[layer_data['type']]
            layer = layer_type(**layer_data['config'])
            self.layers.append(layer)
            
            # Set parameters
            for param_name, param_value in layer_data['params'].items():
                layer.params[param_name] = np.array(param_value)
