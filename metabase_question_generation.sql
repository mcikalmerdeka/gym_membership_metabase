-- Checking the values
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

-- ================================================================================================

-- Check the visit per week statistics
SELECT
    MIN(visit_per_week)::integer as least_visit_per_week,
    CEIL(AVG(visit_per_week)) as avg_visit_per_week,
    MAX(visit_per_week)::integer as most_visit_per_week
FROM gym_members;

-- ================================================================================================

-- Check the gym duration statistics
SELECT
    MIN(avg_time_in_gym)::integer as shortest_time_in_gym,
    CEIL(AVG(avg_time_in_gym)) as avg_time_in_gym,
    MAX(avg_time_in_gym)::integer as longest_time_in_gym
FROM gym_members;

-- ================================================================================================

-- Check in and check out time trends by hour
WITH check_in AS (
    SELECT
        EXTRACT(HOUR FROM avg_time_check_in::time) as check_in_hour,
        COUNT(*) as check_in_count
    FROM gym_members
    GROUP BY EXTRACT(HOUR FROM avg_time_check_in::time)
    ORDER BY check_in_hour
),
check_out AS (
    SELECT
        EXTRACT(HOUR FROM avg_time_check_out::time) as check_out_hour,
        COUNT(*) as check_out_count
    FROM gym_members
    GROUP BY EXTRACT(HOUR FROM avg_time_check_out::time)
    ORDER BY check_out_hour
)
SELECT
    COALESCE(check_in_hour, check_out_hour) as check_in_hour,
    check_out_hour::integer as check_out_hour,
    COALESCE(check_in_count, 0) as check_in_count,
    check_out_count
FROM check_out
LEFT JOIN check_in
    ON check_in_hour = check_out_hour;

-- ================================================================================================

-- Number of unique group lessons
WITH expanded_lessons AS (
    SELECT id, UNNEST(string_to_array(fav_group_lesson, ', ')) AS lesson
    FROM gym_members
    WHERE fav_group_lesson IS NOT NULL
)
SELECT COUNT(DISTINCT lesson) as unique_group_lessons
FROM expanded_lessons;

-- ================================================================================================

-- Gym members most popular group lessons, drinks and personal trainers
WITH expanded_lessons AS (
    SELECT UNNEST(string_to_array(fav_group_lesson, ', ')) AS lesson
    FROM gym_members
    WHERE fav_group_lesson IS NOT NULL
),
expanded_drinks AS (
    SELECT UNNEST(string_to_array(fav_drink, ', ')) AS drink
    FROM gym_members
    WHERE fav_drink IS NOT NULL
),
expanded_trainers AS (
    SELECT UNNEST(string_to_array(name_personal_trainer, ', ')) AS trainer
    FROM gym_members
    WHERE name_personal_trainer IS NOT NULL
),

-- Combine the data
combined_data AS (
    SELECT 
        'Group Lesson' as category,
        lesson as item,
        COUNT(*) as count
    FROM expanded_lessons
    GROUP BY lesson
    UNION ALL
    SELECT 
        'Drink' as category,
        drink,
        COUNT(*) as count
    FROM expanded_drinks
    GROUP BY drink
    UNION ALL
    SELECT 
        'Trainer' as category,
        trainer,
        COUNT(*) as count
    FROM expanded_trainers
    GROUP BY trainer
),

-- Assign ranks to the data
assigned_ranks AS (
    SELECT
        category,
        item,
        count,
        RANK() OVER(PARTITION BY category ORDER BY count DESC) as rank
    FROM combined_data
)

-- Get the most popular items for each category
SELECT
    category,
    item
FROM assigned_ranks
WHERE rank = 1;

-- ================================================================================================

-- Days per week member count with expanded days
WITH expanded_days AS (
    SELECT 
        id,
        UNNEST(string_to_array(days_per_week, ', ')) AS day_of_week
    FROM gym_members
)
SELECT 
    day_of_week,
    COUNT(*) as number_of_members
FROM expanded_days
GROUP BY day_of_week
ORDER BY 
    CASE 
        WHEN day_of_week = 'Mon' THEN 1
        WHEN day_of_week = 'Tue' THEN 2
        WHEN day_of_week = 'Wed' THEN 3
        WHEN day_of_week = 'Thu' THEN 4
        WHEN day_of_week = 'Fri' THEN 5
        WHEN day_of_week = 'Sat' THEN 6
        WHEN day_of_week = 'Sun' THEN 7
    END;

-- Count total number of rows
SELECT COUNT(*) as total_rows 
FROM gym_members;

-- Count total number of columns
SELECT COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'gym_members';

-- Get detailed column information
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'gym_members'
ORDER BY ordinal_position;

-- Count rows with additional information (counting the male and female distribution)
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
    COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count,
    COUNT(CASE WHEN personal_training = true THEN 1 END) as personal_training_count
FROM gym_members;

-- Check 
SELECT rolname, rolcanlogin, rolsuper FROM pg_roles;
SELECT * FROM pg_roles;
SELECT usename, passwd FROM pg_shadow;