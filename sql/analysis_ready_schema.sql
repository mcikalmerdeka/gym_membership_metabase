-- Analysis-ready schema for the gym membership data.
-- Run from the repository root with psql so the relative \copy paths resolve.

CREATE TABLE IF NOT EXISTS gym_members_wide (
    id INTEGER PRIMARY KEY,
    gender VARCHAR(10),
    birthday DATE,
    age INTEGER,
    abonoment_type VARCHAR(20),
    visit_per_week INTEGER,
    attend_group_lesson BOOLEAN,
    avg_time_check_in TIME,
    avg_time_check_out TIME,
    avg_time_in_gym INTEGER,
    drink_abo BOOLEAN,
    personal_training BOOLEAN,
    name_personal_trainer VARCHAR(50),
    uses_sauna BOOLEAN,
    visit_mon BOOLEAN,
    visit_tue BOOLEAN,
    visit_wed BOOLEAN,
    visit_thu BOOLEAN,
    visit_fri BOOLEAN,
    visit_sat BOOLEAN,
    visit_sun BOOLEAN,
    lesson_bodybalance BOOLEAN,
    lesson_bodypump BOOLEAN,
    lesson_hit BOOLEAN,
    lesson_kickboxen BOOLEAN,
    lesson_lesmiles BOOLEAN,
    lesson_pilates BOOLEAN,
    lesson_running BOOLEAN,
    lesson_spinning BOOLEAN,
    lesson_xcore BOOLEAN,
    lesson_yoga BOOLEAN,
    lesson_zumba BOOLEAN,
    n_fav_lessons INTEGER,
    drink_berry_boost BOOLEAN,
    drink_black_currant BOOLEAN,
    drink_coconut_pineapple BOOLEAN,
    drink_lemon BOOLEAN,
    drink_orange BOOLEAN,
    drink_passion_fruit BOOLEAN,
    n_fav_drinks INTEGER
);

CREATE TABLE IF NOT EXISTS gym_members_clean (
    id INTEGER PRIMARY KEY,
    gender VARCHAR(10),
    birthday DATE,
    age INTEGER,
    abonoment_type VARCHAR(20),
    visit_per_week INTEGER,
    attend_group_lesson BOOLEAN,
    avg_time_check_in TIME,
    avg_time_check_out TIME,
    avg_time_in_gym INTEGER,
    drink_abo BOOLEAN,
    personal_training BOOLEAN,
    name_personal_trainer VARCHAR(50),
    uses_sauna BOOLEAN
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

\copy gym_members_wide FROM 'data/analysis_ready/gym_members_wide.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy gym_members_clean FROM 'data/analysis_ready/members.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy gym_member_days FROM 'data/analysis_ready/member_days.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy gym_member_lessons FROM 'data/analysis_ready/member_lessons.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy gym_member_drinks FROM 'data/analysis_ready/member_drinks.csv' WITH (FORMAT csv, HEADER true, NULL '');
