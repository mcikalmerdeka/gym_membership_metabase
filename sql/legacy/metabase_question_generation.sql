-- ======================================================================== Individual Key Metrics ========================================================================

-- Amount of membership
SELECT
    COUNT(*) as total_members
FROM gym_members;

-- Amount of personal trainer
SELECT
    COUNT(DISTINCT name_personal_trainer) as total_personal_trainers 
FROM gym_members;

-- Number of unique group lessons
WITH expanded_lessons AS (
    SELECT id, UNNEST(string_to_array(fav_group_lesson, ', ')) AS lesson
    FROM gym_members
    WHERE fav_group_lesson IS NOT NULL
)
SELECT COUNT(DISTINCT lesson) as unique_group_lessons
FROM expanded_lessons;

-- ======================================================================== Charts Generation ========================================================================

-- Grouping by abonoment type
SELECT
    abonoment_type,
    COUNT(*) as total_members
FROM gym_members
GROUP BY abonoment_type;

-- Grouping by gender
SELECT
    gender,
    COUNT(*) as total_members
FROM gym_members
GROUP BY gender;

-- Grouping by usage of personal trainer or not
SELECT
    personal_training,
    COUNT(*) as total_members
FROM gym_members
GROUP BY personal_training;

-- Grouping by usage of sauna or not
SELECT
    uses_sauna,
    COUNT(*) as total_members
FROM gym_members
GROUP BY uses_sauna;

-- Grouping by attendance of group lesson or not
SELECT
    attend_group_lesson,
    COUNT(*) as total_members
FROM gym_members
GROUP BY attend_group_lesson;

-- Grouping by drink abonoment or not
SELECT
    drink_abo as drink_abonoment,
    COUNT(*) as total_members
FROM gym_members
GROUP BY drink_abo;

-- ================================================================================================

-- Check the visit per week statistics
SELECT
    MIN(visit_per_week)::integer as least_visit_per_week,
    CEIL(AVG(visit_per_week)) as avg_visit_per_week,
    MAX(visit_per_week)::integer as most_visit_per_week
FROM gym_members;

-- ================================================================================================

-- Check the gym session duration statistics
SELECT
    MIN(avg_time_in_gym)::integer as shortest_time_in_gym,
    CEIL(AVG(avg_time_in_gym)) as avg_time_in_gym,
    MAX(avg_time_in_gym)::integer as longest_time_in_gym
FROM gym_members;

-- ================================================================================================

-- Check in and check out time trends by hour
WITH check_in AS (
    SELECT
        EXTRACT(HOUR FROM avg_time_check_in) as check_in_hour,
        COUNT(*) as check_in_count
    FROM gym_members
    GROUP BY EXTRACT(HOUR FROM avg_time_check_in)
    ORDER BY check_in_hour
),
check_out AS (
    SELECT
        EXTRACT(HOUR FROM avg_time_check_out) as check_out_hour,
        COUNT(*) as check_out_count
    FROM gym_members
    GROUP BY EXTRACT(HOUR FROM avg_time_check_out)
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
    item,
    rank as popularity_rank
FROM assigned_ranks
WHERE rank IN (1, 2);

-- ================================================================================================

-- Days per week member count with expanded days
WITH expanded_days AS (
    SELECT 
        id,
        UNNEST(string_to_array(day_of_week, ', ')) AS day_of_week
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