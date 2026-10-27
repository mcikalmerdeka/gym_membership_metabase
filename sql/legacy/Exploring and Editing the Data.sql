-- ======================================================================== Further exploration of the data ========================================================================

-- Checking original table
SELECT
    id,
    gender,
    birthday
    age,
    abonoment_type,
    visit_per_week,
    days_per_week,
    attend_group_lesson,
    fav_group_lesson,
    avg_time_check_in,
    avg_time_check_out,
    avg_time_in_gym,
    drink_abo,
    fav_drink,
    personal_training,
    name_personal_trainer,
    uses_sauna
FROM gym_members;

-- Checking the original table processed
SELECT
    id,
    gender,
    birthday,
    age,
    abonoment_type,
    visit_per_week,
    attend_group_lesson,
    avg_time_check_in,
    avg_time_check_out,
    avg_time_in_gym,
    drink_abo,
    personal_training,
    uses_sauna,
    name_personal_trainer,
    UNNEST(string_to_array(fav_group_lesson, ', ')) AS lesson,
    UNNEST(string_to_array(fav_drink, ', ')) AS drink,
    UNNEST(string_to_array(days_per_week, ', ')) AS day_of_week
FROM gym_members;

-- Checking the processed table (gym_members_normalized)
SELECT *
FROM gym_members_normalized;

-- Check all available tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- Count total number of columns for both tables
SELECT 
    'gym_members' as table_name,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'gym_members'
UNION ALL
SELECT 
    'gym_members_normalized' as table_name,
    COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'gym_members_normalized';

-- Get detailed column information
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'gym_members'
ORDER BY ordinal_position;

-- Get detailed column information for the normalized table
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'gym_members_normalized'
ORDER BY ordinal_position;

-- Count rows with additional information (counting the male and female distribution)
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
    COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count,
    COUNT(CASE WHEN personal_training = true THEN 1 END) as personal_training_count
FROM gym_members;

-- Check the roles and users
SELECT rolname, rolcanlogin, rolsuper FROM pg_roles;
SELECT * FROM pg_roles;
SELECT usename, passwd FROM pg_shadow;

-- ======================================================================== Small Preprocessing on Data Types =========================================================================

-- Change boolean columns to character varying
ALTER TABLE gym_members 
    ALTER COLUMN attend_group_lesson TYPE VARCHAR USING attend_group_lesson::VARCHAR;

ALTER TABLE gym_members 
    ALTER COLUMN drink_abo TYPE VARCHAR USING drink_abo::VARCHAR;

ALTER TABLE gym_members 
    ALTER COLUMN personal_training TYPE VARCHAR USING personal_training::VARCHAR;

ALTER TABLE gym_members 
    ALTER COLUMN uses_sauna TYPE VARCHAR USING uses_sauna::VARCHAR;

-- Rename the column to match desired schema
ALTER TABLE gym_members 
    RENAME COLUMN days_per_week TO day_of_week;

ALTER TABLE gym_members 
    ALTER COLUMN fav_group_lesson TYPE VARCHAR USING fav_group_lesson::VARCHAR;

ALTER TABLE gym_members 
    ALTER COLUMN fav_drink TYPE VARCHAR USING fav_drink::VARCHAR;

ALTER TABLE gym_members 
    ALTER COLUMN day_of_week TYPE VARCHAR USING day_of_week::VARCHAR;

-- Verify the changes match the desired schema
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'gym_members'
ORDER BY ordinal_position;
