import numpy as np
import re
from collections import Counter
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

class AdvancedTextProcessor:
    """Advanced text processing dengan NLTK dan Sastrawi"""
    
    def __init__(self, language='indonesian', max_vocab_size=10000, max_sequence_length=100):
        self.language = language
        self.max_vocab_size = max_vocab_size
        self.max_sequence_length = max_sequence_length
        
        # Initialize stemmers and stopword removers
        if language == 'english':
            self.stemmer = PorterStemmer()
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                nltk.download('stopwords')
                self.stop_words = set(stopwords.words('english'))
        else:
            factory = StemmerFactory()
            self.stemmer = factory.create_stemmer()
            stopword_factory = StopWordRemoverFactory()
            self.stop_words = stopword_factory.get_stop_words()
            
        self.vocab = {}
        self.reverse_vocab = {}
        self.vocab_size = 0
        
    def advanced_preprocess(self, text, remove_stopwords=True, stem=True, 
                          remove_punct=True, remove_numbers=True):
        """Advanced text preprocessing"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove numbers
        if remove_numbers:
            text = re.sub(r'\d+', '', text)
            
        # Remove punctuation
        if remove_punct:
            text = re.sub(r'[^\w\s]', ' ', text)
            
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        if remove_stopwords:
            tokens = [token for token in tokens if token not in self.stop_words]
            
        # Stemming
        if stem:
            if self.language == 'english':
                tokens = [self.stemmer.stem(token) for token in tokens]
            else:
                tokens = [self.stemmer.stem(token) for token in tokens]
                
        # Remove short tokens
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def build_vocabulary(self, texts, min_freq=2):
        """Build vocabulary from texts dengan frequency filtering"""
        word_freq = Counter()
        
        for text in texts:
            tokens = self.advanced_preprocess(text)
            word_freq.update(tokens)
            
        # Filter by minimum frequency
        filtered_words = {word: freq for word, freq in word_freq.items() if freq >= min_freq}
        
        # Sort by frequency
        sorted_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)
        
        # Limit vocabulary size
        if len(sorted_words) > self.max_vocab_size - 2:
            sorted_words = sorted_words[:self.max_vocab_size - 2]
            
        # Build vocabulary
        self.vocab = {'<PAD>': 0, '<UNK>': 1}
        for idx, (word, freq) in enumerate(sorted_words):
            self.vocab[word] = idx + 2
            
        self.reverse_vocab = {idx: word for word, idx in self.vocab.items()}
        self.vocab_size = len(self.vocab)
        
    def texts_to_sequences(self, texts):
        """Convert texts to sequences of integers"""
        sequences = []
        for text in texts:
            tokens = self.advanced_preprocess(text)
            sequence = [self.vocab.get(token, self.vocab['<UNK>']) for token in tokens]
            sequences.append(sequence)
        return sequences
    
    def pad_sequences(self, sequences, maxlen=None):
        """Pad sequences to uniform length"""
        maxlen = maxlen or self.max_sequence_length
        padded_sequences = np.zeros((len(sequences), maxlen), dtype=int)
        
        for i, sequence in enumerate(sequences):
            if len(sequence) > maxlen:
                # Truncate
                padded_sequences[i] = sequence[:maxlen]
            else:
                # Pad
                padded_sequences[i, :len(sequence)] = sequence
                
        return padded_sequences
    
    def create_embedding_matrix(self, embedding_dim=100):
        """Create embedding matrix dengan random initialization"""
        embedding_matrix = np.random.normal(0, 0.1, (self.vocab_size, embedding_dim))
        embedding_matrix[0] = 0  # Padding token
        return embedding_matrix
    
    def fit_transform(self, texts):
        """Build vocabulary and transform texts in one step"""
        self.build_vocabulary(texts)
        sequences = self.texts_to_sequences(texts)
        return self.pad_sequences(sequences)
