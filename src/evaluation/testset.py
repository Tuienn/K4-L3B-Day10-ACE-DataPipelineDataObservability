from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Tạo bộ evaluation set (Ground Truth) gồm 10 câu hỏi thuộc 4 dạng bài toán:
    1. summary: Hỏi tóm tắt nội dung chính của bài báo.
    2. authors: Hỏi về tác giả công trình nghiên cứu.
    3. date: Hỏi thời điểm xuất bản.
    4. categories: Hỏi về lĩnh vực chuyên môn.

    Mỗi câu hỏi có định dạng:
    {
      "id": "eval_001",
      "question_type": "summary",
      "question": "What is the summary of the paper '<Title>'?",
      "ground_truth": "<Nội dung câu đầu tóm tắt chuẩn>",
      "ground_truth_doc_ids": ["<DOI bài báo>"]
    }
    """
    if len(df) < 4:
        raise ValueError(f"DataFrame must contain at least 4 rows to build test set, got {len(df)}.")

    target_path = Path(output_path)

    # 10 câu hỏi phân bổ qua 4 dạng bài toán: summary (3), authors (3), date (2), categories (2)
    question_types = [
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
    ]

    test_set: list[dict[str, Any]] = []
    num_rows = len(df)

    for i, q_type in enumerate(question_types):
        row = df.iloc[i % num_rows]
        title = str(row["title"]).strip()
        paper_id = str(row["paper_id"]).strip()

        if q_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(str(row["summary"]))
        elif q_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = str(row["authors_joined"])
        elif q_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = str(row["published"])
        elif q_type == "categories":
            question = f"What categories does the paper '{title}' belong to?"
            ground_truth = str(row["categories_joined"])
        else:
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(str(row["summary"]))

        test_set.append(
            {
                "id": f"eval_{i + 1:03d}",
                "question_type": q_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    write_json(target_path, test_set)
    return test_set

