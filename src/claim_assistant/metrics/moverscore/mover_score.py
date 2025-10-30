import json
from collections import defaultdict

import numpy as np

from claim_assistant.metrics.moverscore.moverscore import word_mover_score


def sentence_score(hypothesis: str, references: list[str], trace=0):
    idf_dict_hyp: defaultdict[str, float] = defaultdict(lambda: 1.0)
    idf_dict_ref: defaultdict[str, float] = defaultdict(lambda: 1.0)

    hypothesis_list = [hypothesis] * len(references)

    sentence_score = 0

    scores = word_mover_score(
        references,
        hypothesis_list,
        idf_dict_ref,
        idf_dict_hyp,
        stop_words=[],
        n_gram=1,
        remove_subwords=False,
    )

    sentence_score = np.mean(scores)

    if trace > 0:
        print(hypothesis, references, sentence_score)

    return sentence_score


def load_json_file(file_path: str) -> dict:
    """Load JSON data from file."""
    with open(file_path, "r") as f:
        return json.load(f)


def normalize_field_name(name: str) -> str:
    """Normalize field names for comparison."""
    return name.lower().replace(" ", "_").replace("-", "_")


def compare_extraction_results(
    extracted_file: str = None,
    ground_truth_file: str = None,
):
    """Compare extracted answers with ground truth answers using MoverScore."""

    # Default file paths if not provided
    if extracted_file is None:
        extracted_file = "data/forms/dwc/extracted_answers.json"
    if ground_truth_file is None:
        ground_truth_file = "data/forms/dwc/form_answers.json"

    try:
        # Load the data files
        extracted_data = load_json_file(extracted_file)
        form_answers = load_json_file(ground_truth_file)
    except FileNotFoundError as e:
        print(f"Error loading file: {e}")
        return None

    # Get the extracted data (first item in the data array)
    extracted_answers = extracted_data["data"][0]

    # Create a mapping from normalized question to answer for form_answers
    ground_truth = {}
    for item in form_answers:
        question_normalized = normalize_field_name(item["question"])
        ground_truth[question_normalized] = item["answer"]

    print("Comparing extracted answers with ground truth using MoverScore:")
    print("=" * 70)

    total_score = 0
    field_count = 0
    comparisons = []

    # Compare each field
    for field_name, extracted_value in extracted_answers.items():
        # Normalize the field name for matching
        normalized_field = normalize_field_name(field_name)

        # Handle special case for address_line vs address_line_1
        if normalized_field == "address_line_1" and "address_line" in ground_truth:
            normalized_field = "address_line"

        if normalized_field in ground_truth:
            ground_truth_value = ground_truth[normalized_field]

            # Calculate MoverScore between extracted and ground truth
            try:
                score = sentence_score(str(extracted_value), [str(ground_truth_value)])

                print(f"\nField: {field_name}")
                print(f"Ground Truth: {ground_truth_value}")
                print(f"Extracted:    {extracted_value}")
                print(f"MoverScore:   {score:.4f}")

                # Determine match quality
                if score >= 0.9:
                    match_quality = "EXCELLENT"
                elif score >= 0.7:
                    match_quality = "GOOD"
                elif score >= 0.5:
                    match_quality = "FAIR"
                else:
                    match_quality = "POOR"

                print(f"Match Quality: {match_quality}")
                print("-" * 50)

                comparisons.append(
                    {
                        "field": field_name,
                        "ground_truth": ground_truth_value,
                        "extracted": extracted_value,
                        "score": score,
                        "quality": match_quality,
                    },
                )

                total_score += score
                field_count += 1

            except Exception as e:
                print(f"Error calculating score for field '{field_name}': {e}")
        else:
            print(
                f"\nField '{field_name}' (normalized: '{normalized_field}') not found in ground truth data",
            )

    # Calculate average score
    if field_count > 0:
        average_score = total_score / field_count
        print("\nOverall Results:")
        print("=" * 50)
        print(f"Total fields compared: {field_count}")
        print(f"Average MoverScore: {average_score:.4f}")
        print(f"Total score: {total_score:.4f}")

        # Show quality distribution
        quality_counts: dict[str, int] = {}
        for comp in comparisons:
            quality = comp["quality"]
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        print("\nQuality Distribution:")
        for quality, count in quality_counts.items():
            print(f"  {quality}: {count} fields")

        # Show best and worst performing fields
        if comparisons:
            comparisons.sort(key=lambda x: x["score"], reverse=True)
            print(
                f"\nBest performing field: {comparisons[0]['field']} (Score: {comparisons[0]['score']:.4f})",
            )
            print(
                f"Worst performing field: {comparisons[-1]['field']} (Score: {comparisons[-1]['score']:.4f})",
            )

        return {
            "average_score": average_score,
            "total_score": total_score,
            "field_count": field_count,
            "comparisons": comparisons,
        }
    else:
        print("No matching fields found for comparison")
        return None


if __name__ == "__main__":
    # Run comparison when script is executed directly
    compare_extraction_results()
