class Callback:
    """Base callback class"""
    
    def on_epoch_begin(self, epoch, logs=None):
        pass
        
    def on_epoch_end(self, epoch, logs=None):
        pass
        
    def on_batch_begin(self, batch, logs=None):
        pass
        
    def on_batch_end(self, batch, logs=None):
        pass

class EarlyStopping(Callback):
    """Early stopping callback"""
    
    def __init__(self, monitor='val_loss', patience=10, min_delta=0, restore_best_weights=True):
        self.monitor = monitor
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best_weights = restore_best_weights
        self.wait = 0
        self.best_weights = None
        self.best_epoch = 0
        
    def on_epoch_end(self, epoch, logs=None):
        current = logs.get(self.monitor)
        if current is None:
            return
            
        if self.best_weights is None or current < self.best_score - self.min_delta:
            self.best_score = current
            self.best_epoch = epoch
            self.wait = 0
            if self.restore_best_weights:
                self.best_weights = [layer.params.copy() for layer in self.model.layers]
        else:
            self.wait += 1
            if self.wait >= self.patience:
                self.model.stop_training = True
                if self.restore_best_weights and self.best_weights is not None:
                    for layer, weights in zip(self.model.layers, self.best_weights):
                        layer.params = weights

class ModelCheckpoint(Callback):
    """Model checkpoint callback"""
    
    def __init__(self, filepath, monitor='val_loss', save_best_only=True):
        self.filepath = filepath
        self.monitor = monitor
        self.save_best_only = save_best_only
        self.best_score = float('inf')
        
    def on_epoch_end(self, epoch, logs=None):
        current = logs.get(self.monitor)
        if current is None:
            return
            
        if not self.save_best_only or current < self.best_score:
            self.best_score = current
            self.model.save(self.filepath)

class LearningRateScheduler(Callback):
    """Learning rate scheduler"""
    
    def __init__(self, schedule):
        self.schedule = schedule
        
    def on_epoch_begin(self, epoch, logs=None):
        new_lr = self.schedule(epoch)
        self.model.optimizer.learning_rate = new_lr
