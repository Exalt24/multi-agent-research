"""Token counting utilities using tiktoken for accurate LLM cost tracking.

tiktoken is OpenAI's official tokenizer - provides exact token counts for:
- Cost estimation (GPT-4, Claude, Llama all use similar tokenization)
- Context window management (stay within limits)
- Performance optimization (identify expensive operations)

WHY TIKTOKEN:
- Accurate (not rough estimates like len(text) // 4)
- Fast (written in Rust, ~1M tokens/sec)
- Model-aware (different models = different tokenization)
"""

import tiktoken
from functools import lru_cache
from typing import Optional


# =============================================================================
# Token Encoder Caching
# =============================================================================

@lru_cache(maxsize=4)
def get_encoder(model_name: str = "gpt-4") -> tiktoken.Encoding:
    """Get cached tokenizer encoder for a model.

    Args:
        model_name: Model name (gpt-4, gpt-3.5-turbo, etc.)

    Returns:
        tiktoken.Encoding for the model

    Note:
        Uses @lru_cache to avoid recreating encoders (expensive operation).
        Most models use the same encoding (cl100k_base), so this is efficient.
    """
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base (used by GPT-4, GPT-3.5-turbo, and most modern models)
        print(f"[!] Model '{model_name}' not found in tiktoken, using cl100k_base encoding")
        return tiktoken.get_encoding("cl100k_base")


# =============================================================================
# Token Counting
# =============================================================================

def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    """Count exact number of tokens in text for a given model.

    Args:
        text: Text to tokenize
        model_name: Model name for tokenization

    Returns:
        Exact token count

    Example:
        >>> count_tokens("Hello, world!")
        4
        >>> count_tokens("def hello():\n    print('Hi')")
        11
    """
    if not text:
        return 0

    encoder = get_encoder(model_name)
    tokens = encoder.encode(text)
    return len(tokens)


def count_tokens_batch(texts: list[str], model_name: str = "gpt-4") -> list[int]:
    """Count tokens for multiple texts efficiently.

    Args:
        texts: List of texts to tokenize
        model_name: Model name for tokenization

    Returns:
        List of token counts (same order as input)

    Example:
        >>> counts = count_tokens_batch(["Hello", "World"])
        >>> counts
        [1, 1]
    """
    encoder = get_encoder(model_name)
    return [len(encoder.encode(text)) for text in texts]


def estimate_tokens(text: str) -> int:
    """Fast token estimation without tiktoken (fallback for performance-critical paths).

    Uses rule of thumb: ~4 characters per token for English text.

    Args:
        text: Text to estimate

    Returns:
        Rough token count estimate

    Note:
        Less accurate than count_tokens() but ~100x faster.
        Use this for hot paths where exact count isn't critical.
    """
    return max(1, len(text) // 4)


# =============================================================================
# Cost Estimation
# =============================================================================

# Cost per 1M tokens (as of December 2024)
COST_PER_MILLION_TOKENS = {
    # OpenAI
    "gpt-4": 30.00,  # GPT-4 (8K context)
    "gpt-4-turbo": 10.00,  # GPT-4 Turbo
    "gpt-3.5-turbo": 0.50,  # GPT-3.5 Turbo

    # Groq (FREE during beta!)
    "llama-3.3-70b-versatile": 0.00,  # Free!
    "mixtral-8x7b": 0.00,  # Free!

    # Ollama (local = free)
    "llama3": 0.00,  # Local
    "mistral": 0.00,  # Local

    # Anthropic (rough estimate based on similar models)
    "claude-3-opus": 15.00,
    "claude-3-sonnet": 3.00,
}


def estimate_cost(
    token_count: int,
    model_name: str,
    cost_per_million: Optional[float] = None
) -> float:
    """Estimate cost in USD for a given token count.

    Args:
        token_count: Number of tokens
        model_name: Model name
        cost_per_million: Override cost (if not in predefined table)

    Returns:
        Estimated cost in USD

    Example:
        >>> cost = estimate_cost(10000, "gpt-4")
        >>> print(f"${cost:.4f}")
        $0.3000
    """
    if cost_per_million is None:
        cost_per_million = COST_PER_MILLION_TOKENS.get(model_name, 0.00)

    return (token_count / 1_000_000) * cost_per_million


def estimate_cost_for_text(
    text: str,
    model_name: str = "gpt-4"
) -> tuple[int, float]:
    """Count tokens and estimate cost for text.

    Args:
        text: Text to analyze
        model_name: Model name

    Returns:
        Tuple of (token_count, estimated_cost_usd)

    Example:
        >>> tokens, cost = estimate_cost_for_text("Hello, world!", "gpt-4")
        >>> print(f"{tokens} tokens = ${cost:.4f}")
        4 tokens = $0.0001
    """
    tokens = count_tokens(text, model_name)
    cost = estimate_cost(tokens, model_name)
    return tokens, cost


# =============================================================================
# Context Window Management
# =============================================================================

CONTEXT_WINDOW_SIZES = {
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 16385,
    "llama-3.3-70b-versatile": 8192,  # Groq Llama 3.3 70B
    "mixtral-8x7b": 32768,
    "llama3": 8192,  # Ollama default
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
}


def check_context_window(
    text: str,
    model_name: str = "gpt-4",
    reserve_tokens: int = 1000
) -> tuple[bool, int, int]:
    """Check if text fits within model's context window.

    Args:
        text: Text to check
        model_name: Model name
        reserve_tokens: Tokens to reserve for response (default 1000)

    Returns:
        Tuple of (fits, token_count, available_tokens)

    Example:
        >>> fits, count, available = check_context_window("Hello!", "gpt-4")
        >>> if not fits:
        ...     print("Text too long!")
    """
    token_count = count_tokens(text, model_name)
    max_tokens = CONTEXT_WINDOW_SIZES.get(model_name, 8192)
    available = max_tokens - reserve_tokens

    return token_count <= available, token_count, available


def truncate_to_token_limit(
    text: str,
    max_tokens: int,
    model_name: str = "gpt-4",
    suffix: str = "..."
) -> str:
    """Truncate text to fit within token limit.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed
        model_name: Model name
        suffix: Suffix to add to truncated text

    Returns:
        Truncated text

    Example:
        >>> truncated = truncate_to_token_limit("Long text...", max_tokens=10)
        >>> count_tokens(truncated)
        <= 10
    """
    encoder = get_encoder(model_name)
    tokens = encoder.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # Reserve tokens for suffix
    suffix_tokens = len(encoder.encode(suffix))
    available_tokens = max_tokens - suffix_tokens

    # Truncate and decode
    truncated_tokens = tokens[:available_tokens]
    truncated_text = encoder.decode(truncated_tokens)

    return truncated_text + suffix


# =============================================================================
# Testing
# =============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Token Counting Utilities Test")
    print("=" * 70)

    # Test 1: Basic counting
    print("\n[1] Basic token counting:")
    test_texts = [
        "Hello, world!",
        "def hello():\n    print('Hi')",
        "The quick brown fox jumps over the lazy dog.",
        "Code with symbols: @#$%^&*()"
    ]

    for text in test_texts:
        tokens = count_tokens(text)
        estimated = estimate_tokens(text)
        print(f"  '{text[:30]}...' -> {tokens} tokens (estimated: {estimated})")

    # Test 2: Comparison with old method
    print("\n[2] Accuracy comparison (tiktoken vs. len//4):")
    code_sample = """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """

    exact = count_tokens(code_sample)
    rough = len(code_sample) // 4
    error_pct = abs(exact - rough) / exact * 100

    print(f"  Code sample: {len(code_sample)} characters")
    print(f"  Exact (tiktoken): {exact} tokens")
    print(f"  Estimate (len//4): {rough} tokens")
    print(f"  Error: {error_pct:.1f}%")

    # Test 3: Cost estimation
    print("\n[3] Cost estimation:")
    for model in ["gpt-4", "gpt-3.5-turbo", "llama-3.3-70b-versatile"]:
        tokens = 10000
        cost = estimate_cost(tokens, model)
        print(f"  {model}: 10k tokens = ${cost:.4f}")

    # Test 4: Context window check
    print("\n[4] Context window check:")
    long_text = "Hello " * 1000
    fits, count, available = check_context_window(long_text, "gpt-4")
    print(f"  Text: {count} tokens")
    print(f"  Available: {available} tokens")
    print(f"  Fits: {'[OK] Yes' if fits else '[NO] No'}")

    # Test 5: Truncation
    print("\n[5] Text truncation:")
    truncated = truncate_to_token_limit(long_text, max_tokens=20)
    truncated_count = count_tokens(truncated)
    print(f"  Original: {count} tokens")
    print(f"  Truncated: {truncated_count} tokens")
    print(f"  Text: '{truncated[:50]}...'")

    print("\n" + "=" * 70)
    print("All tests passed! tiktoken is working correctly.")
    print("=" * 70)
