#!/usr/bin/env python3
"""Test embedding model functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

from rag.embeddings import EmbeddingModel


def main():
    print("=" * 80)
    print("TEST 1: Embedding Model")
    print("=" * 80)

    # Initialize model
    print("\n1. Initializing embedding model...")
    embedder = EmbeddingModel()
    print(f"   Model: {embedder.model_name}")
    print(f"   Dimension: {embedder.get_dimension()}")

    # Test single encode
    print("\n2. Testing single text encoding...")
    text = "def hello(): print('world')"
    vector = embedder.encode(text)
    print(f"   Input: {text}")
    print(f"   Output shape: {vector.shape}")
    print(f"   Expected shape: (768,)")
    assert vector.shape == (768,), f"Expected (768,), got {vector.shape}"
    assert embedder.get_dimension() == 768
    print("   ✓ Single encoding works")

    # Test empty string
    print("\n3. Testing empty string handling...")
    empty_vector = embedder.encode("")
    print(f"   Empty string vector shape: {empty_vector.shape}")
    assert empty_vector.shape == (768,)
    print("   ✓ Empty string handled gracefully")

    # Test batch encode
    print("\n4. Testing batch encoding...")
    texts = ["code 1", "code 2", "code 3"]
    vectors = embedder.encode_batch(texts)
    print(f"   Input: {len(texts)} texts")
    print(f"   Output shape: {vectors.shape}")
    print(f"   Expected shape: (3, 768)")
    assert vectors.shape == (3, 768), f"Expected (3, 768), got {vectors.shape}"
    print("   ✓ Batch encoding works")

    # Test empty batch
    print("\n5. Testing empty batch...")
    empty_batch = embedder.encode_batch([])
    print(f"   Empty batch shape: {empty_batch.shape}")
    assert empty_batch.shape == (0, 768)
    print("   ✓ Empty batch handled gracefully")

    # Test semantic similarity
    print("\n6. Testing semantic similarity...")
    code1 = "def authenticate_user(username, password): return True"
    code2 = "def login_user(user, pwd): return validate_credentials(user, pwd)"
    code3 = "def calculate_fibonacci(n): return fib(n-1) + fib(n-2)"

    vec1 = embedder.encode(code1)
    vec2 = embedder.encode(code2)
    vec3 = embedder.encode(code3)

    # Calculate cosine similarity
    import numpy as np

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    sim_1_2 = cosine_similarity(vec1, vec2)
    sim_1_3 = cosine_similarity(vec1, vec3)

    print(f"   Similarity (auth vs login): {sim_1_2:.4f}")
    print(f"   Similarity (auth vs fibonacci): {sim_1_3:.4f}")
    print(f"   Auth and login should be more similar than auth and fibonacci")
    assert sim_1_2 > sim_1_3, "Authentication functions should be more similar to each other"
    print("   ✓ Semantic similarity works correctly")

    print("\n" + "=" * 80)
    print("✅ ALL EMBEDDING MODEL TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
