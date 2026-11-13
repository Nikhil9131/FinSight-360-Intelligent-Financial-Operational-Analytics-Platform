-- ============================================================
-- FinSight 360 — Date Dimension Table
-- File: database/schema/002_create_dim_date.sql
-- Description: Calendar dimension spanning 2022-01-01 to 2027-12-31
--              Enables time-intelligence in SQL and DAX.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_date (
    date_key          INTEGER PRIMARY KEY,           -- YYYYMMDD format
    full_date         DATE NOT NULL UNIQUE,
    day_of_week       INTEGER NOT NULL,              -- 1=Monday … 7=Sunday (ISO)
    day_name          VARCHAR(10) NOT NULL,
    day_of_month      INTEGER NOT NULL,
    day_of_year       INTEGER NOT NULL,
    week_of_year      INTEGER NOT NULL,              -- ISO week number
    month_number      INTEGER NOT NULL,
    month_name        VARCHAR(10) NOT NULL,
    month_short       VARCHAR(3) NOT NULL,
    quarter           INTEGER NOT NULL,
    quarter_name      VARCHAR(2) NOT NULL,           -- Q1, Q2, Q3, Q4
    year              INTEGER NOT NULL,
    fiscal_year       INTEGER NOT NULL,              -- Same as calendar year (Jan fiscal start)
    fiscal_quarter    INTEGER NOT NULL,
    is_weekend        BOOLEAN NOT NULL,
    is_month_start    BOOLEAN NOT NULL,
    is_month_end      BOOLEAN NOT NULL,
    is_quarter_start  BOOLEAN NOT NULL,
    is_quarter_end    BOOLEAN NOT NULL,
    is_year_start     BOOLEAN NOT NULL,
    is_year_end       BOOLEAN NOT NULL,
    year_month        VARCHAR(7) NOT NULL,           -- 'YYYY-MM'
    year_quarter      VARCHAR(7) NOT NULL            -- 'YYYY-Q1'
);

COMMENT ON TABLE dim_date IS 'Calendar dimension table for time-intelligence in analytics';

-- ─── Populate dim_date: 2022-01-01 to 2027-12-31 ────────────
INSERT INTO dim_date
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER                          AS date_key,
    d                                                         AS full_date,
    EXTRACT(ISODOW FROM d)::INTEGER                           AS day_of_week,
    TO_CHAR(d, 'Day')                                         AS day_name,
    EXTRACT(DAY FROM d)::INTEGER                              AS day_of_month,
    EXTRACT(DOY FROM d)::INTEGER                              AS day_of_year,
    EXTRACT(WEEK FROM d)::INTEGER                             AS week_of_year,
    EXTRACT(MONTH FROM d)::INTEGER                            AS month_number,
    TO_CHAR(d, 'Month')                                       AS month_name,
    TO_CHAR(d, 'Mon')                                         AS month_short,
    EXTRACT(QUARTER FROM d)::INTEGER                          AS quarter,
    'Q' || EXTRACT(QUARTER FROM d)::INTEGER                   AS quarter_name,
    EXTRACT(YEAR FROM d)::INTEGER                             AS year,
    EXTRACT(YEAR FROM d)::INTEGER                             AS fiscal_year,
    EXTRACT(QUARTER FROM d)::INTEGER                          AS fiscal_quarter,
    EXTRACT(ISODOW FROM d) IN (6, 7)                          AS is_weekend,
    EXTRACT(DAY FROM d) = 1                                   AS is_month_start,
    d = (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::DATE  AS is_month_end,
    d = DATE_TRUNC('quarter', d)::DATE                        AS is_quarter_start,
    d = (DATE_TRUNC('quarter', d) + INTERVAL '3 months - 1 day')::DATE AS is_quarter_end,
    EXTRACT(DOY FROM d) = 1                                   AS is_year_start,
    (EXTRACT(MONTH FROM d) = 12 AND EXTRACT(DAY FROM d) = 31) AS is_year_end,
    TO_CHAR(d, 'YYYY-MM')                                     AS year_month,
    TO_CHAR(d, 'YYYY') || '-Q' || EXTRACT(QUARTER FROM d)::INTEGER AS year_quarter
FROM generate_series('2022-01-01'::DATE, '2027-12-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_key) DO NOTHING;
