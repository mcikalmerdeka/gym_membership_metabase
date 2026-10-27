from pathlib import Path

import pandas as pd
import pytest
from pandas.api.types import is_bool_dtype

from scripts import build_analysis_ready as bar


@pytest.fixture(scope="module")
def source() -> pd.DataFrame:
    return bar.load_source(bar.SOURCE_PATH)


@pytest.fixture(scope="module")
def tables(source: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return bar.build_tables(source)


def test_wide_has_one_row_per_member_and_no_multi_value_columns(
    tables: dict[str, pd.DataFrame],
) -> None:
    wide = tables["wide"]

    assert len(wide) == 1_000
    assert wide["id"].is_unique
    assert not {"days_per_week", "fav_group_lesson", "fav_drink"} & set(wide.columns)
    assert len(wide.columns) == len(bar.WIDE_COLUMNS)

    expected_flags = set(bar.DAY_COLUMNS + bar.LESSON_COLUMNS + bar.DRINK_COLUMNS)
    assert expected_flags <= set(wide.columns)
    for column in expected_flags:
        assert is_bool_dtype(wide[column]), f"{column} should be boolean"


def test_wide_one_hot_columns_match_source_lists(
    tables: dict[str, pd.DataFrame], source: pd.DataFrame
) -> None:
    wide = tables["wide"].set_index("id")

    for _, member in source.iterrows():
        member_id = int(member["id"])

        expected_days = set(bar.split_values(member["days_per_week"]))
        actual_days = {
            day for day in bar.DAYS if bool(wide.at[member_id, f"visit_{day.lower()}"])
        }
        assert actual_days == expected_days

        expected_lessons = set(bar.split_values(member["fav_group_lesson"]))
        actual_lessons = {
            lesson
            for lesson in bar.LESSONS
            if bool(wide.at[member_id, bar.lesson_column(lesson)])
        }
        assert actual_lessons == expected_lessons

        expected_drinks = set(bar.split_values(member["fav_drink"]))
        actual_drinks = {
            drink
            for drink in bar.DRINKS
            if bool(wide.at[member_id, bar.drink_column(drink)])
        }
        assert actual_drinks == expected_drinks

        assert int(wide.at[member_id, "n_fav_lessons"]) == len(expected_lessons)
        assert int(wide.at[member_id, "n_fav_drinks"]) == len(expected_drinks)
        assert bool(wide.at[member_id, "attend_group_lesson"]) == bool(expected_lessons)
        assert bool(wide.at[member_id, "drink_abo"]) == bool(expected_drinks)


def test_star_tables_have_expected_grain_and_row_counts(
    tables: dict[str, pd.DataFrame], source: pd.DataFrame
) -> None:
    members = tables["members"]
    days = tables["days"]
    lessons = tables["lessons"]
    drinks = tables["drinks"]

    assert len(members) == 1_000
    assert members["id"].is_unique
    assert list(days.columns) == ["id", "day", "day_order"]
    assert list(lessons.columns) == ["id", "lesson"]
    assert list(drinks.columns) == ["id", "drink"]

    expected_days = sum(len(bar.split_values(value)) for value in source["days_per_week"])
    expected_lessons = sum(
        len(bar.split_values(value)) for value in source["fav_group_lesson"]
    )
    expected_drinks = sum(len(bar.split_values(value)) for value in source["fav_drink"])

    assert len(days) == expected_days == 2_682
    assert len(lessons) == expected_lessons == 1_003
    assert len(drinks) == expected_drinks == 719

    assert not days.duplicated(["id", "day"]).any()
    assert not lessons.duplicated(["id", "lesson"]).any()
    assert not drinks.duplicated(["id", "drink"]).any()

    assert set(days["day"]) <= set(bar.DAYS)
    assert set(lessons["lesson"]) <= set(bar.LESSONS)
    assert set(drinks["drink"]) <= set(bar.DRINKS)
    assert set(days["day_order"]) == set(range(1, 8))


def test_star_tables_do_not_mix_categories(tables: dict[str, pd.DataFrame]) -> None:
    assert list(tables["days"].columns) == ["id", "day", "day_order"]
    assert list(tables["lessons"].columns) == ["id", "lesson"]
    assert list(tables["drinks"].columns) == ["id", "drink"]
    assert "lesson" not in tables["days"].columns
    assert "drink" not in tables["days"].columns
    assert "day" not in tables["lessons"].columns
    assert "day" not in tables["drinks"].columns


def test_star_tables_are_sorted_for_readability(
    tables: dict[str, pd.DataFrame],
) -> None:
    days = tables["days"]
    lessons = tables["lessons"]
    drinks = tables["drinks"]

    assert days.equals(days.sort_values(["id", "day_order"]).reset_index(drop=True))
    assert lessons.equals(lessons.sort_values(["id", "lesson"]).reset_index(drop=True))
    assert drinks.equals(drinks.sort_values(["id", "drink"]).reset_index(drop=True))


def test_scalar_columns_are_analysis_ready(tables: dict[str, pd.DataFrame]) -> None:
    wide = tables["wide"]

    assert wide["birthday"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()
    assert wide["Age"].dtype == "int64"
    assert wide["visit_per_week"].dtype == "int64"
    assert wide["avg_time_in_gym"].dtype == "int64"
    assert wide["n_fav_lessons"].dtype == "int64"
    assert wide["n_fav_drinks"].dtype == "int64"

    for column in ["attend_group_lesson", "drink_abo", "personal_training", "uses_sauna"]:
        assert is_bool_dtype(wide[column]), f"{column} should be boolean"

    required = [
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
    for column in required:
        assert not wide[column].isna().any(), f"{column} should never be missing"
        if wide[column].dtype == "string":
            assert (wide[column].str.strip() == wide[column]).all()


def test_validate_tables_accepts_valid_output_and_rejects_corruption(
    tables: dict[str, pd.DataFrame], source: pd.DataFrame
) -> None:
    bar.validate_tables(tables, source)

    corrupted_wide = {name: table.copy() for name, table in tables.items()}
    first_id = int(corrupted_wide["wide"].at[0, "id"])
    column = bar.lesson_column(bar.LESSONS[0])
    corrupted_wide["wide"].loc[
        corrupted_wide["wide"]["id"] == first_id, column
    ] = ~corrupted_wide["wide"].loc[corrupted_wide["wide"]["id"] == first_id, column]
    with pytest.raises(ValueError, match="lesson|one-hot|count"):
        bar.validate_tables(corrupted_wide, source)

    corrupted_days = {name: table.copy() for name, table in tables.items()}
    corrupted_days["days"] = corrupted_days["days"].iloc[:-1].copy()
    with pytest.raises(ValueError, match="row count|days"):
        bar.validate_tables(corrupted_days, source)

    corrupted_scalars = {name: table.copy() for name, table in tables.items()}
    for table_name in ["wide", "members"]:
        corrupted_scalars[table_name].loc[0, "gender"] = "Other"
    with pytest.raises(ValueError, match="scalar|source|gender"):
        bar.validate_tables(corrupted_scalars, source)


def test_star_tables_round_trip_to_source_lists(
    tables: dict[str, pd.DataFrame], source: pd.DataFrame
) -> None:
    days = tables["days"]
    lessons = tables["lessons"]
    drinks = tables["drinks"]

    for _, member in source.iterrows():
        member_id = int(member["id"])

        assert set(days.loc[days["id"] == member_id, "day"]) == set(
            bar.split_values(member["days_per_week"])
        )
        assert set(lessons.loc[lessons["id"] == member_id, "lesson"]) == set(
            bar.split_values(member["fav_group_lesson"])
        )
        assert set(drinks.loc[drinks["id"] == member_id, "drink"]) == set(
            bar.split_values(member["fav_drink"])
        )


def test_write_tables_writes_all_csvs(
    tmp_path: Path, tables: dict[str, pd.DataFrame]
) -> None:
    bar.write_tables(tables, tmp_path)

    for key, filename in bar.TABLE_FILES.items():
        output = tmp_path / filename
        assert output.exists(), f"{filename} was not written"
        written = pd.read_csv(output, keep_default_na=False)
        assert len(written) == len(tables[key])
        assert list(written.columns) == list(tables[key].columns)


def test_data_dictionary_and_schema_are_generated(
    tmp_path: Path, tables: dict[str, pd.DataFrame]
) -> None:
    dictionary = tmp_path / "data_dictionary.md"
    schema = tmp_path / "analysis_ready_schema.sql"

    bar.write_data_dictionary(tables, dictionary)
    bar.write_schema_sql(schema)

    dictionary_text = dictionary.read_text(encoding="utf-8")
    schema_text = schema.read_text(encoding="utf-8")

    assert "2,682" in dictionary_text
    assert "1,003" in dictionary_text
    assert "719" in dictionary_text
    assert "deprecated" in dictionary_text.lower()
    assert "2025-01-01" in dictionary_text

    for table in [
        "gym_members_wide",
        "gym_members_clean",
        "gym_member_days",
        "gym_member_lessons",
        "gym_member_drinks",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema_text
    assert "FOREIGN KEY" in schema_text
    assert "TRUNCATE TABLE" in schema_text
