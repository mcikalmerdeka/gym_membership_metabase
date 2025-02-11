-- Checking the values
SELECT *
FROM gym_members;

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