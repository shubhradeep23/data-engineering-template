-- Athena serving-layer examples (run in console or CLI against workgroup from terraform output).
-- Replace DATABASE_NAME with terraform output glue_catalog_database.

-- After Glue crawlers finish, list tables:
-- SHOW TABLES IN DATABASE_NAME;

-- Example: daily volumes from curated aggregates (column names depend on crawler schema).
-- SELECT dt, source, row_count
-- FROM DATABASE_NAME.curated_summary_or_similar
-- WHERE dt >= DATE '2025-01-01'
-- ORDER BY dt DESC, row_count DESC
-- LIMIT 100;

-- Ad hoc exploration of staging Parquet (adjust table name from Glue catalog).
-- SELECT *
-- FROM DATABASE_NAME.staging_some_table
-- LIMIT 50;
