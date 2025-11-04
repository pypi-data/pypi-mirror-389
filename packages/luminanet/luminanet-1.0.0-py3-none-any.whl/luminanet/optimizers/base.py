class Optimizer:
    """Base optimizer class"""
    
    def __init__(self, learning_rate=0.001, clipnorm=None, clipvalue=None):
        self.learning_rate = learning_rate
        self.clipnorm = clipnorm
        self.clipvalue = clipvalue
        self.iterations = 0
        
    def apply_gradients(self, grads, params, layer_id):
        """Apply gradients to parameters"""
        raise NotImplementedError
        
    def _clip_gradients(self, grads):
        """Apply gradient clipping"""
        if self.clipnorm is not None:
            norm = sum(np.sum(g**2) for g in grads.values())
            if norm > self.clipnorm:
                scale = self.clipnorm / (norm + 1e-7)
                for key in grads:
                    grads[key] *= scale
                    
        elif self.clipvalue is not None:
            for key in grads:
                grads[key] = np.clip(grads[key], -self.clipvalue, self.clipvalue)
                
        return grads
