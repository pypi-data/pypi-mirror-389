"""Given a list of questions and answers, output JSONL for Items.

This is for bootstrapping benchmarks from existing data.

Example usage:
>>> from commoneval import ROOT, makeitems
>>> questions = ["What does the Bible say is God’s purpose for my life?",
  "Who am I in Christ, and how does that shape my identity?",
  "How do I find meaning in Christ apart from my accomplishments?",]
>>> destpath = ROOT.parent / "eval-Larson/data/eng/larson-commonchristian"
>>> writer = makeitems.QuestionWriter(questions=questions,
  identifier_prefix="lcc", outpath=destpath / f"{destpath.name}.jsonl")

"""

import unicodecsv
from pathlib import Path

import item


class QuestionWriter:
    """Write items to a JSONL file.

    This assumes you have questions (prompts) but no answers (responses).
    """

    def __init__(
        self,
        questions: list[str],
        identifier_prefix: str,
        outpath: Path,
        modality: item.Modality = item.Modality.LONGPROSE,
    ) -> None:
        """Initialize the writer."""
        self.id_index: int = 0
        with outpath.open("w", encoding="utf-8") as f:
            for question in questions:
                itm = item.OpenEndedItem(
                    identifier=f"{identifier_prefix}{self.id_index:04d}",
                    prompt=question,
                    modality=modality,
                    response="",
                )
                itm.write_jsonline(f)
                self.id_index += 1


class SubjectQuestionWriter:
    """Write items to a JSONL file.

    This assumes you have pairs of questions (prompts) with subjects,
    but no answers (responses).

    """

    def __init__(
        self,
        items: list[str],
        identifier_prefix: str,
        outpath: Path,
        modality: item.Modality = item.Modality.LONGPROSE,
    ) -> None:
        """Initialize the writer."""
        self.id_index: int = 0
        with outpath.open("w", encoding="utf-8") as f:
            for subject, question in items:
                itm = item.OpenEndedItem(
                    identifier=f"{identifier_prefix}{self.id_index:04d}",
                    prompt=question,
                    modality=modality,
                    response="",
                    _otherargs={"subject": subject},
                )
                itm.write_jsonline(f)
                self.id_index += 1


class CSVMCQuestionWriter:
    """Read multiple questions from CSV and write items to a JSONL file.

    Assumes some standard column headers and 4 answer choices.

    """

    def __init__(
        self,
        inpath: Path,
        outpath: Path,
        modality: item.Modality = item.Modality.CHOICEOF4,
    ) -> None:
        """Initialize the writer."""
        with inpath.open("rb") as f:
            reader = unicodecsv.DictReader(f)
            self.items = [row for row in reader]
        with outpath.open("w", encoding="utf-8") as f:
            for itemdict in self.items:
                # print(itemdict["correct_answer"])
                # choices = {itemdict[letter] for letter in ["A", "B", "C", "D"]}
                # print(choices)
                try:
                    itemdict["correct_answer"] = int(itemdict["correct_answer"])
                except ValueError:
                    raise ValueError(
                        f"correct_answer must be int: got {itemdict['correct_answer']}."
                    )
                itm = item.ClosedSetItem(
                    identifier=itemdict["id"],
                    modality=modality,
                    prompt=itemdict["question"],
                    response=itemdict["correct_answer"],
                    choices=[itemdict[str(i)] for i in range(4)],
                    _otherargs={
                        "bias_type": itemdict.get("bias_type", ""),
                        "rationale": itemdict.get("rationale", ""),
                    },
                )
                itm.write_jsonline(f)
