"""
LuminaNet - Deep Learning Framework Pure Python
Illuminate Your AI Journey with Minimal Dependencies
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Core imports
from .core.activations import ActivationFunctions
from .core.initializers import Initializers
from .core.regularizers import Regularizers
from .core.constraints import Constraints
from .core.layers import Layer, Dense

# Advanced layers
from .layers.advanced import Dropout
from .layers.convolutional import Conv2D, MaxPooling2D
from .layers.recurrent import LSTM

# Optimizers
from .optimizers.sgd import SGD
from .optimizers.adam import Adam
from .optimizers.rmsprop import RMSprop

# Loss functions
from .losses.loss_functions import LossFunctions

# Models
from .models.model import NeuralNetwork

# Text processing
from .text.processor import AdvancedTextProcessor

# Utils
from .utils.callbacks import Callback, EarlyStopping, ModelCheckpoint, LearningRateScheduler

# Example function
def illuminate():
    """Introduction to LuminaNet"""
    print("=== 🌟 LuminaNet Framework ===")
    print("Deep Learning with Pure Python")
    print("Dependencies: numpy, scipy, nltk, sastrawi")
    print("Ready for Termux and restricted environments!")
    print("Let's illuminate your AI journey! 🚀")

__all__ = [
    # Core
    'ActivationFunctions', 'Initializers', 'Regularizers', 'Constraints',
    'Layer', 'Dense',
    
    # Layers
    'Dropout', 'Conv2D', 'MaxPooling2D', 'LSTM',
    
    # Optimizers
    'SGD', 'Adam', 'RMSprop',
    
    # Losses
    'LossFunctions',
    
    # Models
    'NeuralNetwork',
    
    # Text Processing
    'AdvancedTextProcessor',
    
    # Utils
    'Callback', 'EarlyStopping', 'ModelCheckpoint', 'LearningRateScheduler',
    
    # Functions
    'illuminate'
]
