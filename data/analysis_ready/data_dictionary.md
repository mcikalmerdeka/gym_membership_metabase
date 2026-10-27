# Gym Membership Analysis-Ready Data

Generated from `data/gym_membership_cleaned.csv` by `scripts/build_analysis_ready.py`.

## Output files

| File | Grain | Rows |
|---|---|---:|
| `gym_members_wide.csv` | One row per member, with boolean preference indicators | 1,000 |
| `members.csv` | One row per member, scalar attributes only | 1,000 |
| `member_days.csv` | One row per member-day | 2,682 |
| `member_lessons.csv` | One row per member-lesson | 1,003 |
| `member_drinks.csv` | One row per member-drink | 719 |

## Wide table

`gym_members_wide.csv` keeps the original scalar columns and replaces the
three comma-separated columns with:

- **Visit days:** `visit_mon` through `visit_sun` (7 boolean columns).
  `visit_per_week` equals the sum of these flags.
- **Favourite lessons:** one boolean column per lesson, prefixed `lesson_`.
  The lesson vocabulary is: BodyBalance, BodyPump, HIT, Kickboxen, LesMiles, Pilates, Running, Spinning, XCore, Yoga, Zumba.
- **Favourite drinks:** one boolean column per drink, prefixed `drink_`.
  The drink vocabulary is: berry_boost, black_currant, coconut_pineapple, lemon, orange, passion_fruit.
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
- Exact bridge-table row counts: 2,682 member-days,
  1,003 member-lessons, and 719 member-drinks.
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

`data/gym_membership_cleaned.csv` is left unchanged. Day values are: Mon, Tue, Wed, Thu, Fri, Sat, Sun.
