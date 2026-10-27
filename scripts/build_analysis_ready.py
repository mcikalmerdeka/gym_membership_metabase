"""Build analysis-ready gym membership tables from the cleaned source CSV.

The source file stores three multi-valued attributes as comma-separated text:
days_per_week, fav_group_lesson, and fav_drink. This module expands them into:

1. a wide, one-row-per-member table with boolean indicator columns, and
2. a small star schema with one bridge table per multi-valued attribute.

The source file is never modified.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas.api.types import is_bool_dtype, is_integer_dtype

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "data" / "gym_membership_cleaned.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis_ready"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "analysis_ready_schema.sql"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_ORDER = {day: index for index, day in enumerate(DAYS, start=1)}

# Canonical spellings found in the source data.
LESSONS = [
    "BodyBalance",
    "BodyPump",
    "HIT",
    "Kickboxen",
    "LesMiles",
    "Pilates",
    "Running",
    "Spinning",
    "XCore",
    "Yoga",
    "Zumba",
]
DRINKS = [
    "berry_boost",
    "black_currant",
    "coconut_pineapple",
    "lemon",
    "orange",
    "passion_fruit",
]

SCALAR_COLUMNS = [
    "id",
    "gender",
    "birthday",
    "Age",
    "abonoment_type",
    "visit_per_week",
    "attend_group_lesson",
    "avg_time_check_in",
    "avg_time_check_out",
    "avg_time_in_gym",
    "drink_abo",
    "personal_training",
    "name_personal_trainer",
    "uses_sauna",
]
DAYS_SOURCE_COLUMN = "days_per_week"
LESSONS_SOURCE_COLUMN = "fav_group_lesson"
DRINKS_SOURCE_COLUMN = "fav_drink"
BOOL_COLUMNS = [
    "attend_group_lesson",
    "drink_abo",
    "personal_training",
    "uses_sauna",
]
TIME_COLUMNS = ["avg_time_check_in", "avg_time_check_out"]
INTEGER_SOURCE_COLUMNS = ["id", "Age", "visit_per_week", "avg_time_in_gym"]

DAY_COLUMNS = [f"visit_{day.lower()}" for day in DAYS]
LESSON_COLUMNS = [f"lesson_{lesson.lower()}" for lesson in LESSONS]
DRINK_COLUMNS = [f"drink_{drink}" for drink in DRINKS]
WIDE_COLUMNS = (
    SCALAR_COLUMNS
    + DAY_COLUMNS
    + LESSON_COLUMNS
    + ["n_fav_lessons"]
    + DRINK_COLUMNS
    + ["n_fav_drinks"]
)

TABLE_FILES = {
    "wide": "gym_members_wide.csv",
    "members": "members.csv",
    "days": "member_days.csv",
    "lessons": "member_lessons.csv",
    "drinks": "member_drinks.csv",
}


def lesson_column(lesson: str) -> str:
    """Return the wide-table column name for a lesson."""
    return f"lesson_{lesson.lower()}"


def drink_column(drink: str) -> str:
    """Return the wide-table column name for a drink."""
    return f"drink_{drink}"


def split_values(value: object) -> list[str]:
    """Split a comma-separated source field into clean, non-empty tokens."""
    if value is None or pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [token.strip() for token in text.split(",") if token.strip()]


def _to_whole_int(series: pd.Series, name: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="raise")
    if not (numeric % 1 == 0).all():
        raise ValueError(f"{name} contains non-integer values")
    return numeric.astype("int64")


def _to_bool(series: pd.Series, name: str) -> pd.Series:
    normalized = series.astype("string").str.strip().str.lower()
    unknown = set(normalized.unique()) - {"true", "false"}
    if unknown:
        raise ValueError(f"{name} contains unknown boolean values: {sorted(unknown)}")
    return normalized.map({"true": True, "false": False}).astype(bool)


def load_source(path: Path = SOURCE_PATH) -> pd.DataFrame:
    """Load and normalize the scalar columns of the cleaned source CSV."""
    frame = pd.read_csv(path, dtype="string", keep_default_na=False)

    expected = set(SCALAR_COLUMNS) | {
        DAYS_SOURCE_COLUMN,
        LESSONS_SOURCE_COLUMN,
        DRINKS_SOURCE_COLUMN,
    }
    missing = expected - set(frame.columns)
    if missing:
        raise ValueError(f"source CSV is missing columns: {sorted(missing)}")

    for column in INTEGER_SOURCE_COLUMNS:
        frame[column] = _to_whole_int(frame[column], column)

    for column in BOOL_COLUMNS:
        frame[column] = _to_bool(frame[column], column)

    for column in TIME_COLUMNS:
        frame[column] = frame[column].astype("string").str.strip()

    for column in [
        "gender",
        "abonoment_type",
        "name_personal_trainer",
        DAYS_SOURCE_COLUMN,
        LESSONS_SOURCE_COLUMN,
        DRINKS_SOURCE_COLUMN,
    ]:
        frame[column] = frame[column].astype("string").str.strip()

    birth_dates = pd.to_datetime(
        frame["birthday"].astype("string").str[:10],
        format="%Y-%m-%d",
        errors="raise",
    )
    frame["birthday"] = birth_dates.dt.strftime("%Y-%m-%d").astype("string")

    return frame[SCALAR_COLUMNS + [DAYS_SOURCE_COLUMN, LESSONS_SOURCE_COLUMN, DRINKS_SOURCE_COLUMN]]


def build_wide(source: pd.DataFrame) -> pd.DataFrame:
    """Build the one-row-per-member wide table."""
    wide = source[SCALAR_COLUMNS].copy()

    for day in DAYS:
        column = f"visit_{day.lower()}"
        wide[column] = source[DAYS_SOURCE_COLUMN].map(
            lambda value: day in split_values(value)
        ).astype(bool)

    for lesson in LESSONS:
        column = lesson_column(lesson)
        wide[column] = source[LESSONS_SOURCE_COLUMN].map(
            lambda value: lesson in split_values(value)
        ).astype(bool)

    wide["n_fav_lessons"] = source[LESSONS_SOURCE_COLUMN].map(
        lambda value: len(split_values(value))
    ).astype("int64")

    for drink in DRINKS:
        column = drink_column(drink)
        wide[column] = source[DRINKS_SOURCE_COLUMN].map(
            lambda value: drink in split_values(value)
        ).astype(bool)

    wide["n_fav_drinks"] = source[DRINKS_SOURCE_COLUMN].map(
        lambda value: len(split_values(value))
    ).astype("int64")

    return wide[WIDE_COLUMNS]


def _build_bridge(
    source: pd.DataFrame, source_column: str, value_name: str
) -> pd.DataFrame:
    records: list[tuple[int, str]] = []
    for row in source.itertuples(index=False):
        member_id = int(getattr(row, "id"))
        for value in split_values(getattr(row, source_column)):
            records.append((member_id, value))

    frame = pd.DataFrame(records, columns=["id", value_name])
    frame = frame.astype({"id": "int64", value_name: "string"})
    return frame.sort_values(["id", value_name]).reset_index(drop=True)


def build_days(source: pd.DataFrame) -> pd.DataFrame:
    """Build one row per member-day."""
    records: list[tuple[int, str, int]] = []
    for row in source.itertuples(index=False):
        member_id = int(getattr(row, "id"))
        for day in split_values(getattr(row, DAYS_SOURCE_COLUMN)):
            if day not in DAY_ORDER:
                raise ValueError(f"unknown day {day!r} for member {member_id}")
            records.append((member_id, day, DAY_ORDER[day]))

    frame = pd.DataFrame(records, columns=["id", "day", "day_order"]).astype(
        {"id": "int64", "day": "string", "day_order": "int64"}
    )
    return frame.sort_values(["id", "day_order"]).reset_index(drop=True)


def build_tables(source: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build all analysis-ready tables."""
    wide = build_wide(source)
    members = wide[SCALAR_COLUMNS].copy()

    return {
        "wide": wide,
        "members": members,
        "days": build_days(source),
        "lessons": _build_bridge(source, LESSONS_SOURCE_COLUMN, "lesson"),
        "drinks": _build_bridge(source, DRINKS_SOURCE_COLUMN, "drink"),
    }


def _fail(message: str) -> None:
    raise ValueError(message)


def validate_tables(tables: dict[str, pd.DataFrame], source: pd.DataFrame) -> None:
    """Validate schema, row counts, consistency, and round-trip fidelity."""
    required_keys = set(TABLE_FILES)
    missing = required_keys - set(tables)
    if missing:
        _fail(f"missing tables: {sorted(missing)}")

    wide = tables["wide"]
    members = tables["members"]
    days = tables["days"]
    lessons = tables["lessons"]
    drinks = tables["drinks"]

    if list(wide.columns) != WIDE_COLUMNS:
        _fail("wide table columns do not match the expected schema")
    if list(members.columns) != SCALAR_COLUMNS:
        _fail("members table columns do not match the expected schema")
    if list(days.columns) != ["id", "day", "day_order"]:
        _fail("member_days columns must be exactly id, day, day_order")
    if list(lessons.columns) != ["id", "lesson"]:
        _fail("member_lessons columns must be exactly id, lesson")
    if list(drinks.columns) != ["id", "drink"]:
        _fail("member_drinks columns must be exactly id, drink")

    if len(wide) != len(source):
        _fail(f"wide row count mismatch: expected {len(source)}, got {len(wide)}")
    if len(members) != len(source):
        _fail(f"members row count mismatch: expected {len(source)}, got {len(members)}")
    if not wide["id"].is_unique:
        _fail("wide table contains duplicate member ids")
    if not members["id"].is_unique:
        _fail("members table contains duplicate member ids")

    source_indexed = source.set_index("id").sort_index()
    wide_indexed = wide.set_index("id").sort_index()
    if list(wide_indexed.index) != list(source_indexed.index):
        _fail("wide table member ids do not match the source")
    if not members.reset_index(drop=True).equals(
        wide[SCALAR_COLUMNS].reset_index(drop=True)
    ):
        _fail("members table must be the scalar projection of the wide table")

    for column in [column for column in SCALAR_COLUMNS if column != "id"]:
        if not wide_indexed[column].equals(source_indexed[column]):
            _fail(f"scalar column {column} does not match the source")

    expected_days = source_indexed[DAYS_SOURCE_COLUMN].map(lambda value: set(split_values(value)))
    expected_lessons = source_indexed[LESSONS_SOURCE_COLUMN].map(
        lambda value: set(split_values(value))
    )
    expected_drinks = source_indexed[DRINKS_SOURCE_COLUMN].map(
        lambda value: set(split_values(value))
    )

    for day in DAYS:
        column = f"visit_{day.lower()}"
        expected = expected_days.map(lambda values: day in values).astype(bool)
        actual = wide_indexed[column].astype(bool)
        if not actual.equals(expected):
            _fail(f"{column} one-hot flag mismatch for at least one member")

    for lesson in LESSONS:
        column = lesson_column(lesson)
        expected = expected_lessons.map(lambda values: lesson in values).astype(bool)
        actual = wide_indexed[column].astype(bool)
        if not actual.equals(expected):
            _fail(f"{column} one-hot lesson flag mismatch for at least one member")

    for drink in DRINKS:
        column = drink_column(drink)
        expected = expected_drinks.map(lambda values: drink in values).astype(bool)
        actual = wide_indexed[column].astype(bool)
        if not actual.equals(expected):
            _fail(f"{column} one-hot drink flag mismatch for at least one member")

    expected_lesson_count = expected_lessons.map(len).astype("int64")
    expected_drink_count = expected_drinks.map(len).astype("int64")
    expected_day_count = expected_days.map(len).astype("int64")

    if not wide_indexed["n_fav_lessons"].astype("int64").equals(expected_lesson_count):
        _fail("n_fav_lessons count mismatch")
    if not wide_indexed["n_fav_drinks"].astype("int64").equals(expected_drink_count):
        _fail("n_fav_drinks count mismatch")
    if not wide_indexed["visit_per_week"].astype("int64").equals(expected_day_count):
        _fail("visit_per_week does not match the number of visit days")

    expected_attends = (expected_lesson_count > 0)
    if not wide_indexed["attend_group_lesson"].astype(bool).equals(expected_attends):
        _fail("attend_group_lesson does not match lesson membership")
    expected_drink_abo = (expected_drink_count > 0)
    if not wide_indexed["drink_abo"].astype(bool).equals(expected_drink_abo):
        _fail("drink_abo does not match drink membership")
    expected_training = (
        source_indexed["name_personal_trainer"].astype("string").str.len() > 0
    ).astype(bool)
    if not wide_indexed["personal_training"].astype(bool).equals(expected_training):
        _fail("personal_training does not match trainer assignment")

    if len(days) != int(expected_day_count.sum()):
        _fail(f"member_days row count mismatch: expected {int(expected_day_count.sum())}, got {len(days)}")
    if len(lessons) != int(expected_lesson_count.sum()):
        _fail(
            f"member_lessons row count mismatch: expected {int(expected_lesson_count.sum())}, got {len(lessons)}"
        )
    if len(drinks) != int(expected_drink_count.sum()):
        _fail(
            f"member_drinks row count mismatch: expected {int(expected_drink_count.sum())}, got {len(drinks)}"
        )

    for name, frame, value_column in [
        ("member_days", days, "day"),
        ("member_lessons", lessons, "lesson"),
        ("member_drinks", drinks, "drink"),
    ]:
        if frame.duplicated(["id", value_column]).any():
            _fail(f"{name} contains duplicate (id, {value_column}) pairs")
        if not set(frame["id"]) <= set(members["id"]):
            _fail(f"{name} contains member ids missing from members")
        if frame[value_column].isna().any():
            _fail(f"{name} contains missing values")

    if not set(days["day"]) <= set(DAYS):
        _fail("member_days contains an unknown day")
    if not set(lessons["lesson"]) <= set(LESSONS):
        _fail("member_lessons contains an unknown lesson")
    if not set(drinks["drink"]) <= set(DRINKS):
        _fail("member_drinks contains an unknown drink")
    for row in days.itertuples(index=False):
        if DAY_ORDER[str(row.day)] != int(row.day_order):
            _fail("member_days day_order does not match day")

    actual_days = days.groupby("id")["day"].agg(set).to_dict()
    actual_lessons = lessons.groupby("id")["lesson"].agg(set).to_dict()
    actual_drinks = drinks.groupby("id")["drink"].agg(set).to_dict()
    for member_id in source_indexed.index:
        expected_member_id = int(member_id)
        if actual_days.get(expected_member_id, set()) != expected_days.at[member_id]:
            _fail(f"member_days round-trip mismatch for id={expected_member_id}")
        if actual_lessons.get(expected_member_id, set()) != expected_lessons.at[member_id]:
            _fail(f"member_lessons round-trip mismatch for id={expected_member_id}")
        if actual_drinks.get(expected_member_id, set()) != expected_drinks.at[member_id]:
            _fail(f"member_drinks round-trip mismatch for id={expected_member_id}")

    day_flag_columns = DAY_COLUMNS
    if not wide[day_flag_columns].astype(bool).sum(axis=1).astype("int64").equals(
        wide["visit_per_week"].astype("int64")
    ):
        _fail("visit_per_week must equal the number of day one-hot flags")
    if not wide[LESSON_COLUMNS].astype(bool).sum(axis=1).astype("int64").equals(
        wide["n_fav_lessons"].astype("int64")
    ):
        _fail("n_fav_lessons must equal the number of lesson one-hot flags")
    if not wide[DRINK_COLUMNS].astype(bool).sum(axis=1).astype("int64").equals(
        wide["n_fav_drinks"].astype("int64")
    ):
        _fail("n_fav_drinks must equal the number of drink one-hot flags")

    if not wide["birthday"].astype("string").str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        _fail("birthday must use YYYY-MM-DD format")
    for column in ["Age", "visit_per_week", "avg_time_in_gym", "n_fav_lessons", "n_fav_drinks"]:
        if not is_integer_dtype(wide[column]):
            _fail(f"{column} must be an integer column")
    for column in ["attend_group_lesson", "drink_abo", "personal_training", "uses_sauna"]:
        if not is_bool_dtype(wide[column]):
            _fail(f"{column} must be a boolean column")

    required_non_missing = [
        "id",
        "gender",
        "birthday",
        "Age",
        "abonoment_type",
        "visit_per_week",
        "avg_time_check_in",
        "avg_time_check_out",
        "avg_time_in_gym",
        "name_personal_trainer",
    ]
    for column in required_non_missing:
        if wide[column].isna().any():
            _fail(f"{column} contains missing values")
    for column in ["gender", "abonoment_type", "name_personal_trainer"] + TIME_COLUMNS:
        if not (wide[column].astype("string").str.strip() == wide[column].astype("string")).all():
            _fail(f"{column} contains values with leading or trailing whitespace")


def write_tables(tables: dict[str, pd.DataFrame], output_dir: Path = OUTPUT_DIR) -> None:
    """Write the analysis-ready CSV files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in TABLE_FILES.items():
        tables[key].to_csv(
            output_dir / filename,
            index=False,
            encoding="utf-8",
            lineterminator="\n",
        )


def write_data_dictionary(
    tables: dict[str, pd.DataFrame], path: Path = OUTPUT_DIR / "data_dictionary.md"
) -> None:
    """Write a human-readable data dictionary and cleaning record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    day_list = ", ".join(DAYS)
    lesson_list = ", ".join(LESSONS)
    drink_list = ", ".join(DRINKS)

    text = f"""# Gym Membership Analysis-Ready Data

Generated from `data/gym_membership_cleaned.csv` by `scripts/build_analysis_ready.py`.

## Output files

| File | Grain | Rows |
|---|---|---:|
| `gym_members_wide.csv` | One row per member, with boolean preference indicators | {len(tables["wide"]):,} |
| `members.csv` | One row per member, scalar attributes only | {len(tables["members"]):,} |
| `member_days.csv` | One row per member-day | {len(tables["days"]):,} |
| `member_lessons.csv` | One row per member-lesson | {len(tables["lessons"]):,} |
| `member_drinks.csv` | One row per member-drink | {len(tables["drinks"]):,} |

## Wide table

`gym_members_wide.csv` keeps the original scalar columns and replaces the
three comma-separated columns with:

- **Visit days:** `visit_mon` through `visit_sun` (7 boolean columns).
  `visit_per_week` equals the sum of these flags.
- **Favourite lessons:** one boolean column per lesson, prefixed `lesson_`.
  The lesson vocabulary is: {lesson_list}.
- **Favourite drinks:** one boolean column per drink, prefixed `drink_`.
  The drink vocabulary is: {drink_list}.
- **Counts:** `n_fav_lessons` and `n_fav_drinks` preserve the number of
  selected values and equal the sum of the corresponding boolean flags.

The raw `days_per_week`, `fav_group_lesson`, and `fav_drink` columns are not
present in the wide table. They remain available in the source CSV.

## Star schema

- `members.csv` — member id and scalar attributes only.
- `member_days.csv` — `id`, `day`, `day_order` (Monday = 1, Sunday = 7).
- `member_lessons.csv` — `id`, `lesson`.
- `member_drinks.csv` — `id`, `drink`.

Each bridge table joins to `members.id` independently. Do not join the bridge
tables to each other on `id` alone: that would multiply unrelated days,
lessons, and drinks into a cross-product.

## Cleaning rules

- `birthday` was normalized to ISO `YYYY-MM-DD`. The source timestamp component
  was always `00:00:00`, so no time information was lost.
- `Age`, `visit_per_week`, and `avg_time_in_gym` were converted from float-like
  text to integers. All source values were whole numbers.
- Boolean columns use `True`/`False`.
- List tokens were trimmed and split on commas. Values were validated against
  the allowed vocabularies above.
- `name_personal_trainer` is empty when `personal_training` is false.
- The source column name `abonoment_type` is preserved intentionally to avoid
  breaking existing SQL. Treat it as `membership_type`.

## Reference date

`Age` is the source dataset's age snapshot, consistent with an age reference
date of **2025-01-01**. It is not recomputed as of today. Recompute from
`birthday` if a current-age analysis is required.

## Validation

The build validates:

- 1,000 unique member ids.
- Exact bridge-table row counts: {len(tables["days"]):,} member-days,
  {len(tables["lessons"]):,} member-lessons, and {len(tables["drinks"]):,} member-drinks.
- `visit_per_week` equals the number of visit-day flags.
- `attend_group_lesson` equals `n_fav_lessons > 0`.
- `drink_abo` equals `n_fav_drinks > 0`.
- `personal_training` equals whether a trainer is assigned.
- No duplicate `(id, value)` pairs in any bridge table.
- Every value belongs to its allowed vocabulary.
- Re-expanding the star tables reproduces the source lists exactly.

## Deprecated file

`data/gym_membership_cleaned_normalized.csv` is **deprecated**. It was produced
by zipping the three independent lists together positionally, which invents
relationships such as a lesson occurring on a particular day. It contains
2,840 rows and should not be used for analysis. Use the star schema above
instead.

## Source

`data/gym_membership_cleaned.csv` is left unchanged. Day values are: {day_list}.
"""
    path.write_text(text, encoding="utf-8")


def write_schema_sql(path: Path = SCHEMA_PATH) -> None:
    """Write PostgreSQL DDL and psql COPY commands for the output tables."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    wide_columns = [
        "id INTEGER PRIMARY KEY",
        "gender VARCHAR(10)",
        "birthday DATE",
        "age INTEGER",
        "abonoment_type VARCHAR(20)",
        "visit_per_week INTEGER",
        "attend_group_lesson BOOLEAN",
        "avg_time_check_in TIME",
        "avg_time_check_out TIME",
        "avg_time_in_gym INTEGER",
        "drink_abo BOOLEAN",
        "personal_training BOOLEAN",
        "name_personal_trainer VARCHAR(50)",
        "uses_sauna BOOLEAN",
    ]
    wide_columns += [f"{column} BOOLEAN" for column in DAY_COLUMNS]
    wide_columns += [f"{column} BOOLEAN" for column in LESSON_COLUMNS]
    wide_columns.append("n_fav_lessons INTEGER")
    wide_columns += [f"{column} BOOLEAN" for column in DRINK_COLUMNS]
    wide_columns.append("n_fav_drinks INTEGER")

    member_columns = [
        "id INTEGER PRIMARY KEY",
        "gender VARCHAR(10)",
        "birthday DATE",
        "age INTEGER",
        "abonoment_type VARCHAR(20)",
        "visit_per_week INTEGER",
        "attend_group_lesson BOOLEAN",
        "avg_time_check_in TIME",
        "avg_time_check_out TIME",
        "avg_time_in_gym INTEGER",
        "drink_abo BOOLEAN",
        "personal_training BOOLEAN",
        "name_personal_trainer VARCHAR(50)",
        "uses_sauna BOOLEAN",
    ]

    wide_body = ",\n    ".join(wide_columns)
    member_body = ",\n    ".join(member_columns)

    text = f"""-- Analysis-ready schema for the gym membership data.
-- Run from the repository root with psql so the relative \\copy paths resolve.

CREATE TABLE IF NOT EXISTS gym_members_wide (
    {wide_body}
);

CREATE TABLE IF NOT EXISTS gym_members_clean (
    {member_body}
);

CREATE TABLE IF NOT EXISTS gym_member_days (
    id INTEGER NOT NULL,
    day VARCHAR(3) NOT NULL,
    day_order SMALLINT NOT NULL,
    PRIMARY KEY (id, day),
    FOREIGN KEY (id) REFERENCES gym_members_clean(id)
);

CREATE TABLE IF NOT EXISTS gym_member_lessons (
    id INTEGER NOT NULL,
    lesson VARCHAR(50) NOT NULL,
    PRIMARY KEY (id, lesson),
    FOREIGN KEY (id) REFERENCES gym_members_clean(id)
);

CREATE TABLE IF NOT EXISTS gym_member_drinks (
    id INTEGER NOT NULL,
    drink VARCHAR(50) NOT NULL,
    PRIMARY KEY (id, drink),
    FOREIGN KEY (id) REFERENCES gym_members_clean(id)
);

CREATE INDEX IF NOT EXISTS gym_member_days_day_idx
    ON gym_member_days (day);
CREATE INDEX IF NOT EXISTS gym_member_lessons_lesson_idx
    ON gym_member_lessons (lesson);
CREATE INDEX IF NOT EXISTS gym_member_drinks_drink_idx
    ON gym_member_drinks (drink);

-- Re-running this script replaces the contents of the analysis-ready tables.
TRUNCATE TABLE
    gym_member_days,
    gym_member_lessons,
    gym_member_drinks,
    gym_members_clean,
    gym_members_wide
RESTART IDENTITY CASCADE;

\\copy gym_members_wide FROM 'data/analysis_ready/gym_members_wide.csv' WITH (FORMAT csv, HEADER true, NULL '');
\\copy gym_members_clean FROM 'data/analysis_ready/members.csv' WITH (FORMAT csv, HEADER true, NULL '');
\\copy gym_member_days FROM 'data/analysis_ready/member_days.csv' WITH (FORMAT csv, HEADER true, NULL '');
\\copy gym_member_lessons FROM 'data/analysis_ready/member_lessons.csv' WITH (FORMAT csv, HEADER true, NULL '');
\\copy gym_member_drinks FROM 'data/analysis_ready/member_drinks.csv' WITH (FORMAT csv, HEADER true, NULL '');
"""
    path.write_text(text, encoding="utf-8")


def main(output_dir: Path = OUTPUT_DIR) -> None:
    """Build, validate, and write all analysis-ready outputs."""
    output_dir = Path(output_dir)
    source = load_source()
    tables = build_tables(source)
    validate_tables(tables, source)

    write_tables(tables, output_dir)
    write_data_dictionary(tables, output_dir / "data_dictionary.md")
    write_schema_sql(SCHEMA_PATH)

    print(f"Wrote analysis-ready data to {output_dir}")
    for key, filename in TABLE_FILES.items():
        print(f"  {filename}: {len(tables[key]):,} rows")
    print(f"  data_dictionary.md")
    print(f"Wrote PostgreSQL schema to {SCHEMA_PATH}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"directory for generated CSV files (default: {OUTPUT_DIR})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main(_parse_args().output_dir)
