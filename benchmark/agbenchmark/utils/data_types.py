import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, constr, validator


class DifficultyLevel(Enum):
    interface = "interface"
    basic = "basic"
    novice = "novice"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"
    human = "human"


# map from enum to difficulty level (numeric)
DIFFICULTY_MAP = {
    DifficultyLevel.interface: 1,
    DifficultyLevel.basic: 2,
    DifficultyLevel.novice: 3,
    DifficultyLevel.intermediate: 4,
    DifficultyLevel.advanced: 5,
    DifficultyLevel.expert: 6,
    DifficultyLevel.human: 7,
}

STRING_DIFFICULTY_MAP = {e.value: DIFFICULTY_MAP[e] for e in DifficultyLevel}


class Info(BaseModel):
    difficulty: DifficultyLevel
    description: constr(regex=r"^Tests if the agent can.*")
    side_effects: List[str]

    @validator("difficulty", pre=True)
    def difficulty_to_enum(cls: "Info", v: str | DifficultyLevel) -> DifficultyLevel:
        """Convert a string to an instance of DifficultyLevel."""
        if isinstance(v, DifficultyLevel):
            return v

        if isinstance(v, str):
            try:
                return DifficultyLevel(v.lower())
            except ValueError:
                pass

        raise ValueError(f"Cannot convert {v} to DifficultyLevel.")


class Eval(BaseModel):
    type: str
    scoring: Optional[str]
    template: Optional[str]
    examples: Optional[str]

    @validator("scoring", "template", always=True)
    def validate_eval_fields(cls, v, values, field):
        if "type" in values and values["type"] == "llm":
            if v is None:
                raise ValueError(f"{field.name} must be provided when type is 'llm'")
        else:
            if v is not None:
                raise ValueError(f"{field.name} should only exist when type is 'llm'")
        return v

    @validator("scoring")
    def validate_scoring(cls, v):
        if v is not None and v not in ["percentage", "scale", "binary"]:
            raise ValueError(
                "scoring must be either 'percentage', 'scale', or 'binary'"
            )
        return v

    @validator("template")
    def validate_template(cls, v):
        if v is not None and v not in ["rubric", "reference", "question", "custom"]:
            raise ValueError(
                "template must be either 'rubric', 'reference', 'question', or 'custom'"
            )
        return v


class Ground(BaseModel):
    answer: str
    should_contain: Optional[List[str]] = None
    should_not_contain: Optional[List[str]] = None
    files: List[str]
    case_sensitive: Optional[bool] = True
    eval: Eval


class Category(str, Enum):
    DATA = "data"
    GENERALIST = "general"
    CODING = "coding"
    SCRAPE_SYNTHESIZE = "scrape_synthesize"
    GAIA_1 = "GAIA_1"
    GAIA_2 = "GAIA_2"
    GAIA_3 = "GAIA_3"


class ChallengeData(BaseModel):
    name: str
    category: List[Category]
    task: str
    dependencies: List[str]
    cutoff: int
    ground: Ground | Dict[str, Ground]
    info: Info | Dict[str, Info]
    metadata: Optional[Dict[str, Any]] = None

    def serialize(self, path: str) -> None:
        with open(path, "w") as file:
            file.write(self.json())

    def get_data(self) -> dict:
        return self.dict()

    @staticmethod
    def get_json_from_path(json_path: Path | str) -> dict:
        path = Path(json_path).resolve()
        with open(path, "r") as file:
            data = json.load(file)
        return data

    @staticmethod
    def deserialize(path: str) -> "ChallengeData":
        # this script is in root/agbenchmark/utils/define_task_types.py
        script_dir = Path(__file__).resolve().parent.parent.parent
        json_path = script_dir / Path(path)

        with open(json_path, "r") as file:
            data = json.load(file)
        try:
            return ChallengeData(**data)
        except:
            test = "ok"

    def challenge_from_datum(self, file_datum: list[dict[str, Any]]) -> "ChallengeData":
        same_task_data = {
            "name": self.prefix,
            "dependencies": self.dependencies,
            "category": self.shared_category,
            "task": self.task,
            "cutoff": self.cutoff,
        }

        if not self.info:
            same_task_data["info"] = {
                datum["name"]: datum["info"] for datum in file_datum
            }
        else:
            same_task_data["info"] = self.info

        if not self.ground:
            same_task_data["ground"] = {
                datum["name"]: datum["ground"] for datum in file_datum
            }
        else:
            same_task_data["ground"] = self.ground

        return ChallengeData(**same_task_data)

    def challenge_from_test_data(self, data: dict[str, Any]) -> "ChallengeData":
        same_task_data = {
            "name": data["name"],
            "dependencies": data["dependencies"],
            "category": data["category"],
            "info": data["info"],
            "ground": data["ground"],
        }

        if self.same_task:
            same_task_data["category"].extend(self.shared_category)
            same_task_data["task"] = self.task
            same_task_data["cutoff"] = self.cutoff
        else:
            same_task_data["task"] = data["task"]
            same_task_data["cutoff"] = data["cutoff"]

        return ChallengeData(**same_task_data)
