import numpy as np
import nltk

def example_usage():
    """Contoh penggunaan framework LuminaNet"""
    print("=== 🌟 LuminaNet Example Usage ===")
    
    # Download NLTK data jika diperlukan
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
        
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    
    # Import dari LuminaNet
    from luminanet import NeuralNetwork, Dense, AdvancedTextProcessor, LSTM, illuminate
    
    # Tampilkan intro
    illuminate()
    
    # 1. Basic Neural Network Example
    print("\n1. Basic Neural Network (XOR Problem):")
    
    # Data XOR
    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y = np.array([[1, 0], [0, 1], [0, 1], [1, 0]])  # One-hot encoding
    
    # Buat model
    model = NeuralNetwork("XORSolver")
    model.add(Dense(4, activation='relu'))
    model.add(Dense(2, activation='softmax'))
    model.compile(optimizer='adam', learning_rate=0.1, loss='categorical_crossentropy')
    
    # Training
    print("Training neural network...")
    model.train(X, y, epochs=1000, batch_size=4, verbose=False)
    
    # Test
    predictions = model.predict_classes(X)
    print(f"Predictions: {predictions}")
    print(f"Expected:    {np.argmax(y, axis=1)}")
    
    # 2. Text Classification Example
    print("\n2. Text Classification dengan LSTM:")
    
    # Sample data Indonesia
    texts = [
        "saya suka makan nasi goreng",
        "nasi goreng enak sekali", 
        "saya tidak suka sayur",
        "sayur itu sehat dan bergizi",
        "olahraga membuat sehat",
        "makan makanan bergizi"
    ]
    labels = [0, 0, 1, 1, 2, 2]  # 0: makanan, 1: kesehatan, 2: olahraga
    
    # Preprocessing teks
    text_processor = AdvancedTextProcessor(language='indonesian', max_vocab_size=100, max_sequence_length=10)
    X_text = text_processor.fit_transform(texts)
    
    # Convert labels to one-hot
    num_classes = len(np.unique(labels))
    y_text = np.eye(num_classes)[labels]
    
    # Build LSTM model
    lstm_model = NeuralNetwork("IndonesianTextClassifier")
    lstm_model.add(LSTM(32, return_sequences=False))
    lstm_model.add(Dense(32, activation='relu'))
    lstm_model.add(Dense(num_classes, activation='softmax'))
    
    lstm_model.compile(optimizer='adam', learning_rate=0.001, loss='categorical_crossentropy', metrics=['accuracy'])
    
    print("Training LSTM model...")
    lstm_model.train(X_text, y_text, epochs=50, batch_size=2, verbose=False)
    
    # Test prediction
    test_text = "nasi goreng spesial"
    test_X = text_processor.fit_transform([test_text])
    prediction = lstm_model.predict(test_X)
    
    print(f"Text: '{test_text}'")
    print(f"Prediction probabilities: {prediction[0]}")
    print(f"Predicted class: {np.argmax(prediction[0])}")
    
    print("\n✅ All examples completed successfully!")
    print("🎉 LuminaNet is working perfectly!")

if __name__ == "__main__":
    example_usage()
