-- Version 1 of creating table
CREATE TABLE gym_members (
    id SERIAL PRIMARY KEY,
    gender VARCHAR(10),
    birthday TIMESTAMP,
    age NUMERIC(4,1),
    abonoment_type VARCHAR(20),
    visit_per_week NUMERIC(3,1),
    days_per_week TEXT[],
    attend_group_lesson BOOLEAN,
    fav_group_lesson TEXT[],
    avg_time_check_in TIME,
    avg_time_check_out TIME,
    avg_time_in_gym NUMERIC(5,1),
    drink_abo BOOLEAN,
    fav_drink TEXT[],
    personal_training BOOLEAN,
    name_personal_trainer VARCHAR(50),
    uses_sauna BOOLEAN,
    
    -- Add constraints
    CONSTRAINT valid_gender CHECK (gender IN ('Male', 'Female', 'Other')),
    CONSTRAINT valid_abonoment CHECK (abonoment_type IN ('Standard', 'Premium')),
    CONSTRAINT valid_age CHECK (age > 0)
);

-- Add comments for documentation
COMMENT ON TABLE gym_members IS 'Stores gym member profiles and their training preferences';
COMMENT ON COLUMN gym_members.days_per_week IS 'Array of days when member typically visits';
COMMENT ON COLUMN gym_members.fav_group_lesson IS 'Array of preferred group lessons';
COMMENT ON COLUMN gym_members.avg_time_in_gym IS 'Average duration in minutes spent at the gym';

-- Remove existing constraints
ALTER TABLE gym_members
    DROP CONSTRAINT IF EXISTS valid_gender,
    DROP CONSTRAINT IF EXISTS valid_abonoment,
    DROP CONSTRAINT IF EXISTS valid_age;

-- Add constraints back
ALTER TABLE gym_members
    ADD CONSTRAINT valid_gender CHECK (gender IN ('Male', 'Female', 'Other')),
    ADD CONSTRAINT valid_abonoment CHECK (abonoment_type IN ('Standard', 'Premium')),
    ADD CONSTRAINT valid_age CHECK (age > 0);

-- To view all constraints on the table
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'gym_members'::regclass;

-- Version 2 of Creating Table
CREATE TABLE IF NOT EXISTS gym_members (
    id INTEGER PRIMARY KEY,
    gender VARCHAR(10),
    birthday TIMESTAMP,
    age NUMERIC(4,1),
    abonoment_type VARCHAR(20),
    visit_per_week NUMERIC(3,1),
    days_per_week TEXT,  -- Changed from TEXT[] to TEXT for initial import
    attend_group_lesson BOOLEAN,
    fav_group_lesson TEXT,  -- Changed from TEXT[] to TEXT for initial import
    avg_time_check_in TIME,
    avg_time_check_out TIME,
    avg_time_in_gym NUMERIC(5,1),
    drink_abo BOOLEAN,
    fav_drink TEXT,  -- Changed from TEXT[] to TEXT for initial import
    personal_training BOOLEAN,
    name_personal_trainer VARCHAR(50),
    uses_sauna BOOLEAN
);

-- Version 3 of creating table
-- Recreate the table with NULLABLE and explicit parsing
CREATE TABLE gym_members (
    id INTEGER,  -- Change from SERIAL to allow manual ID input
    gender VARCHAR(10),
    birthday TIMESTAMP,
    age NUMERIC(4,1),
    abonoment_type VARCHAR(20),
    visit_per_week NUMERIC(3,1),
    days_per_week TEXT,
    attend_group_lesson BOOLEAN,
    fav_group_lesson TEXT,
    avg_time_check_in TIME,
    avg_time_check_out TIME,
    avg_time_in_gym NUMERIC(5,1),
    drink_abo BOOLEAN,
    fav_drink TEXT,
    personal_training BOOLEAN,
    name_personal_trainer VARCHAR(50),
    uses_sauna BOOLEAN
);

-- Drop the existing table completely
DROP TABLE IF EXISTS gym_members;

-- Import the CSV file version 1
COPY gym_members 
FROM 'E:\Personal Projects\Gym Membership Metabase\gym_membership_cleaned.csv'  -- USE FULL WINDOWS PATH
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ',',
    QUOTE '"',
    ENCODING 'UTF8',
    NULL ''
);

-- Import the CSV file version 2
COPY gym_members FROM 'E:\Personal Projects\Gym Membership Metabase\gym_membership_cleaned.csv' 
WITH (
    FORMAT csv,
    HEADER true,
    DELIMITER ',',
    NULL '',
    QUOTE '"'
);

-- Experiment with inserting values
INSERT INTO gym_members (
    id, gender, birthday, age, abonoment_type, visit_per_week, 
    days_per_week, attend_group_lesson, fav_group_lesson, 
    avg_time_check_in, avg_time_check_out, avg_time_in_gym,
    drink_abo, fav_drink, personal_training, name_personal_trainer, uses_sauna
) VALUES (
    1, 'Female', '1997-04-18', 27.0, 'Premium', 4.0,
    ARRAY['Mon', 'Sat', 'Tue', 'Wed'], TRUE, 
    ARRAY['Kickboxen', 'BodyPump', 'Zumba'],
    '19:31', '21:27', 116.0,
    FALSE, NULL, FALSE, NULL, TRUE
);
