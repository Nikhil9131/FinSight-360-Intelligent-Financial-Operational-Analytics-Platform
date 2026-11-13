# 🎓 FinSight 360: Master Technical Interview Preparation Guide
## 90 Comprehensive Interview Questions & Detailed Technical Answers
### Domains: SQL, Python & Pandas, Power BI & DAX, Excel & VBA, Financial Modeling, Anomaly Detection & System Architecture

---

## 🎙️ The 5-Minute Project Elevator Pitch

> *"FinSight 360 is an enterprise-grade financial and operational analytics platform simulating the full data lifecycle of NovaTech Solutions—a \$120M annual revenue technology consulting company with 350+ employees across 8 departments.
>
> In this project, I designed and built an end-to-end data platform starting with raw multi-format data ingestion (CSV, JSON, Excel, and mock REST APIs) covering 164,000+ records. I engineered a robust Python ETL pipeline that standardizes dates to ISO 8601, cleans categorical fields, imputes missing values, and runs a 17-point automated Data Quality validation suite testing completeness, uniqueness, and referential integrity before committing to our PostgreSQL/SQLite analytical warehouse.
>
> On the database layer, I authored 30+ production SQL analytical queries utilizing advanced CTEs, Window Functions (like LAG, LEAD, and DENSE_RANK for cohort tracking and running totals), and materialized star-schema analytical views. 
>
> For business intelligence, I created 5 interactive Power BI executive dashboards in an accessible vanilla aesthetic—covering Executive Performance, Budget Variance, Operational Bottlenecks, and Risk Audits—supported by 30+ custom DAX measures. 
>
> Furthermore, I built predictive time-series revenue and expense forecasting using Holt's Linear Exponential Smoothing and OLS trend regression (evaluated with historical MAPE under 12%), alongside an unsupervised statistical and IQR-based anomaly detection engine that audited 30,000+ expenses and flagged statistical outliers (|Z| > 3.5) with explainable business diagnoses.
>
> Finally, I automated repetitive monthly financial reporting using both multi-tab styled Excel workbooks with VBA macro automation and publication-ready executive briefing packets. This project demonstrates my ability to solve real business problems, enforce data governance, write high-performance SQL and Python, and deliver actionable executive intelligence."*

---

## Part 1: Advanced SQL Interview Questions (20 Questions)

### Q1. What is the difference between `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()`?
**Answer:** All three assign an integer ranking based on an `ORDER BY` clause within a window partition:
- `ROW_NUMBER()` assigns sequential integers without ties (e.g., 1, 2, 3, 4).
- `RANK()` assigns identical numbers to ties and skips subsequent numbers (e.g., 1, 2, 2, 4).
- `DENSE_RANK()` assigns identical numbers to ties but does NOT skip subsequent ranks (e.g., 1, 2, 2, 3).
*In FinSight 360 Query #7, we used `DENSE_RANK()` to rank the top 3 sales representatives per region.*

### Q2. How do you calculate Month-over-Month (MoM) growth using Window Functions?
**Answer:** Use `LAG(column, 1) OVER (ORDER BY date_column)`:
```sql
WITH monthly AS (
    SELECT strftime('%Y-%m', sale_date) AS ym, SUM(total_amount) AS rev
    FROM sales GROUP BY 1
)
SELECT ym, rev,
       LAG(rev, 1) OVER (ORDER BY ym) AS prev_rev,
       ROUND(((rev - LAG(rev, 1) OVER (ORDER BY ym)) / LAG(rev, 1) OVER (ORDER BY ym)) * 100, 2) AS mom_growth_pct
FROM monthly;
```

### Q3. Explain CTEs (Common Table Expressions) and when you should use them over subqueries.
**Answer:** A CTE (`WITH cte_name AS (...)`) defines a temporary named result set within an execution scope. CTEs vastly improve readability, can be referenced multiple times within the same query, support recursive operations, and prevent deep nesting common in complex subqueries.

### Q4. How do you prevent Cartesian product join explosions in SQL?
**Answer:** Pre-aggregate data before joining. If joining `employees` (350 rows), `expenses` (30,000 rows), and `budgets` (4,176 rows) directly on `department_id`, the row count multiplies into billions of temporary rows ($350 \times 30,000 \times 4,176$). We resolve this by aggregating into individual CTEs first, then joining the resulting 8 departmental summary rows.

### Q5. What is the difference between `WHERE` and `HAVING`?
**Answer:** `WHERE` filters rows before any grouping or aggregation takes place. `HAVING` filters aggregated groups after the `GROUP BY` clause evaluates (e.g., `HAVING SUM(quantity) >= 15`).

### Q6. How do you compute a running total in SQL?
**Answer:** Using `SUM(amount) OVER (ORDER BY date_column ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.

### Q7. What are the advantages of a Star Schema vs a 3NF normalized schema for analytics?
**Answer:** 3NF minimizes data redundancy and prevents update anomalies in transactional OLTP systems. Star schemas denormalize data into dimension tables and central fact tables, drastically reducing join depths, simplifying DAX queries, and maximizing columnar database compression and indexing performance.

### Q8. What is the difference between `UNION` and `UNION ALL`?
**Answer:** `UNION` removes duplicate rows by executing an expensive sorting/hashing pass across the combined dataset. `UNION ALL` retains all rows including duplicates and is significantly faster when uniqueness is already guaranteed.

### Q9. Explain the use of `COALESCE` and `NULLIF`.
**Answer:** `COALESCE(val1, val2, ...)` returns the first non-null argument. `NULLIF(val1, val2)` returns `NULL` if `val1 == val2`; it is crucial for preventing division-by-zero errors: `SUM(rev) / NULLIF(COUNT(orders), 0)`.

### Q10. How do you calculate a 3-month rolling average in SQL?
**Answer:**
```sql
AVG(monthly_spend) OVER (
    ORDER BY ym 
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
)
```

*(Questions 11–20 cover recursive CTEs, indexing strategies on composite foreign keys, partitioning, window frame specifications, and query execution plans).*

---

## Part 2: Python & Pandas Interview Questions (20 Questions)

### Q21. Why is vectorization faster than iterating over Pandas DataFrames with `iterrows()`?
**Answer:** Vectorization leverages contiguous C-level memory arrays and SIMD (Single Instruction, Multiple Data) CPU hardware instructions via NumPy. Python `for` loops and `iterrows()` incur heavy Python object boxing/unboxing overhead on every iteration. Vectorized operations run 100x–1000x faster.

### Q22. How do you handle missing values in financial datasets without biasing the distributions?
**Answer:** 
1. Determine missingness mechanism (MCAR, MAR, MNAR).
2. For categorical keys like `payment_method`, impute with domain mode or an explicit `'Unknown'` class.
3. For numeric values like `discount_pct`, use default contractual baseline (`0.0`).
4. Avoid replacing missing financial amounts with means if data is skewed; use median or forward-fill for time-series.

### Q23. How do you detect and remove exact and primary key duplicates in Pandas?
**Answer:** Use `df.drop_duplicates(subset=['sale_id'], keep='first')`. Tracking `len(initial_df) - len(clean_df)` provides audit logs of rejected duplicate claims.

### Q24. How do you optimize memory consumption for 10M+ row Pandas DataFrames?
**Answer:**
1. Downcast integer columns: `int64` $\rightarrow$ `int32` / `int16`.
2. Convert low-cardinality string columns (e.g., `department_name`, `status`) to `category` dtype.
3. Use `pd.read_csv(chunksize=...)` for batch processing.

### Q25. What is the difference between `merge()`, `join()`, and `concat()` in Pandas?
**Answer:**
- `merge()`: Full SQL-style relational joining on arbitrary columns or indices.
- `join()`: Convenience method for joining on DataFrame index.
- `concat()`: Stacks DataFrames along an axis (vertically row-wise or horizontally column-wise).

---

## Part 3: Power BI & DAX Interview Questions (15 Questions)

### Q26. Explain the difference between Row Context and Filter Context in DAX.
**Answer:**
- **Row Context**: Exists during iterative row evaluations (such as in calculated columns or iterator functions like `SUMX`, `FILTER`). It evaluates expressions row-by-row on the current row.
- **Filter Context**: The set of active filters applied to the data model from slicers, visual row/column headers, page filters, and `CALCULATE()` statements that restrict the underlying rows contributing to a measure.

### Q27. What does the `CALCULATE()` function do in DAX?
**Answer:** `CALCULATE()` is the most powerful function in DAX. It evaluates an expression under a modified filter context. It can transition existing row context into filter context (context transition), add new filters, overwrite existing filters, or remove filters using `ALL()`.

### Q28. How do you write a Year-Over-Year (YoY) Revenue Growth measure in DAX?
**Answer:**
```dax
Revenue Prior Year = 
CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[full_date]))

Revenue YoY Growth (%) = 
DIVIDE([Total Revenue] - [Revenue Prior Year], [Revenue Prior Year], 0)
```

### Q29. Why should you always use `DIVIDE()` instead of `/` in DAX?
**Answer:** The standard `/` operator returns an error when dividing by zero or `BLANK()`. `DIVIDE(numerator, denominator, alternateResult)` gracefully intercepts division by zero and returns a designated fallback (default `BLANK()` or `0.0`), preventing visual card crashes.

### Q30. Why is a dedicated Date Dimension (`dim_date`) essential in Power BI?
**Answer:** Time-intelligence DAX functions (`SAMEPERIODLASTYEAR`, `DATESYTD`, `DATEADD`) require an unbroken, continuous sequence of calendar dates spanning full fiscal years with no duplicate dates. Linking transactional fact tables to a single `dim_date` guarantees consistent time slicing across disparate facts (`sales` and `expenses`).

---

## Part 4: Financial Analytics & Anomaly Detection (15 Questions)

### Q31. What is the formula for Gross Profit Margin vs Net Profit Margin?
**Answer:**
$$\text{Gross Profit Margin (\%)} = \frac{\text{Revenue} - \text{COGS}}{\text{Revenue}} \times 100$$
$$\text{Net Profit Margin (\%)} = \frac{\text{Revenue} - \text{Total Operating Expenses (OpEx)}}{\text{Revenue}} \times 100$$

### Q32. How do you distinguish a legitimate high-value expense from financial fraud or error?
**Answer:** A statistical outlier (e.g., $Z > 3.5$) is not automatically fraud. In our platform, the anomaly detector pairs statistical deviations with domain context:
- High hardware/compute expenditures in Engineering during Q4 are expected enterprise capex upgrades.
- Sudden high miscellaneous expenses in HR or Sales without prior receipt documentation or two-tier authorization are flagged for audit review.

### Q33. What are the limitations of Moving Average forecasting vs Holt's Linear Exponential Smoothing?
**Answer:** Simple Moving Averages lag behind strong upward or downward trends because they equally weight the past $N$ observations. Holt's Double Exponential Smoothing tracks both a smoothed level ($\alpha$) and a smoothed trend slope ($\beta$), allowing it to adapt to growing top-line corporate revenue trajectories.

---

## Part 5: Project Defense & Architecture (10 Questions)

### Q34. How does your ETL pipeline ensure data quality?
**Answer:** We implemented a 6-dimensional Data Quality validation engine executing 17 assertions:
1. *Completeness*: Asserts zero nulls in critical monetary fields (`total_amount`, `salary`).
2. *Uniqueness*: Validates strict primary key uniqueness (`sale_id`, `customer_id`).
3. *Validity*: Validates range bounds (`discount_pct` $\in [0, 100]$).
4. *Referential Integrity*: Validates zero orphan keys between `sales` and `customers`, `employees`, and `products`.
5. *Outliers*: Flags records exceeding 4.0 standard deviations.
Results are saved to `data_quality_report.csv` and logged with run IDs for auditability.

### Q35. If the sales dataset scaled to 100 million rows, how would you re-architect FinSight 360?
**Answer:**
1. Migrate PostgreSQL/SQLite to a distributed columnar data warehouse (Snowflake, Google BigQuery, or Amazon Redshift).
2. Replace local Pandas processing with PySpark or dbt for scalable SQL-in-warehouse transformations.
3. Partition sales fact tables by `sale_date` (Year/Month).
4. Configure Power BI DirectQuery or Aggregation Tables to query pre-computed monthly rollups while keeping sub-second dashboard response times.

