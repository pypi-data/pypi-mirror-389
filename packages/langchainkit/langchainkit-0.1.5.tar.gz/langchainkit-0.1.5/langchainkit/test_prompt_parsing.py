"""Test script for prompt_parsing with batch processing."""

from pydantic import BaseModel
from structured_llm import prompt_parsing
from local_vllm import GeneralLLM
from dotenv import load_dotenv
load_dotenv()


class MathResponse(BaseModel):
    """Response model for math problems."""
    question: str
    answer: int
    explanation: str


def test_batch_prompt_parsing():
    """Test batch prompt_parsing with simple math problems to verify 1-1 correspondence."""

    # Initialize LLM
    llm = GeneralLLM.deepseek_chat()

    # Create batch of simple math problems with expected answers
    test_cases = [
        ("What is 5 + 3?", 8),
        ("What is 10 - 4?", 6),
        ("What is 6 * 7?", 42),
        ("What is 20 / 5?", 4),
        ("What is 15 + 25?", 40),
        ("What is 100 - 37?", 63),
        ("What is 9 * 9?", 81),
        ("What is 144 / 12?", 12),
    ]

    queries = [q for q, _ in test_cases]
    expected_answers = [a for _, a in test_cases]

    print(f"Testing {len(queries)} math problems...")
    print("-" * 80)

    # Run batch processing
    failed_model = MathResponse(
        question="ERROR",
        answer=-999,
        explanation="Failed to process"
    )

    results = prompt_parsing(
        model=MathResponse,
        failed_model=failed_model,
        query=queries,
        llm=llm,
        use_langfuse=False,  # Disable langfuse for testing
        max_concurrency=4
    )

    # Verify 1-1 correspondence
    print("\nVerifying 1-1 correspondence:")
    print("-" * 80)

    all_correct = True
    for i, (query, expected, result) in enumerate(zip(queries, expected_answers, results), 1):
        # Check if question in response matches the input query
        question_match = query.lower() in result.question.lower() or \
                        str(expected) in result.question or \
                        result.question == "ERROR"

        # Check if answer matches expected
        answer_match = result.answer == expected

        status = "✅" if answer_match else "❌"

        print(f"\n[{i}] {status} Query: {query}")
        print(f"    Expected: {expected}")
        print(f"    Got: {result.answer}")
        print(f"    Response Question: {result.question}")
        print(f"    Explanation: {result.explanation[:100]}...")

        if not answer_match:
            all_correct = False
            print(f"    ⚠️  MISMATCH DETECTED!")

    print("\n" + "=" * 80)
    if all_correct:
        print("✅ ALL TESTS PASSED - Perfect 1-1 correspondence maintained!")
    else:
        print("❌ SOME TESTS FAILED - Check mismatches above")
    print("=" * 80)

    return all_correct


def test_single_prompt_parsing():
    """Test single prompt parsing as a baseline."""

    llm = GeneralLLM.deepseek_chat()
    model_name = getattr(llm, "model", None) or getattr(llm, "model_name", None)
    print(f"Using model: {model_name}")

    print("\nTesting single prompt parsing...")
    print("-" * 80)

    failed_model = MathResponse(
        question="ERROR",
        answer=-999,
        explanation="Failed to process"
    )

    result = prompt_parsing(
        model=MathResponse,
        failed_model=failed_model,
        query="What is 7 + 8?",
        llm=llm,
        use_langfuse=False
    )

    print(f"Query: What is 7 + 8?")
    print(f"Expected: 15")
    print(f"Got: {result.answer}")
    print(f"Response Question: {result.question}")
    print(f"Explanation: {result.explanation}")

    success = result.answer == 15
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")

    return success


if __name__ == "__main__":
    print("=" * 80)
    print("Testing prompt_parsing for 1-1 correspondence")
    print("=" * 80)

    # Test single prompt first
    single_success = test_single_prompt_parsing()

    print("\n" * 2)

    # Test batch prompts
    batch_success = test_batch_prompt_parsing()

    print("\n" * 2)
    print("=" * 80)
    print("FINAL RESULTS:")
    print(f"  Single Prompt Test: {'✅ PASSED' if single_success else '❌ FAILED'}")
    print(f"  Batch Prompt Test: {'✅ PASSED' if batch_success else '❌ FAILED'}")
    print("=" * 80)