## Usage

1. Read Alembic tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html.
2. To create a new migration script, run:

    ```bash
    alembic revision -m "Some meaningful description of the migration"
    ```

    to create in warehouse:

    ```bash
    alembic -c ./alembic_warehouse.ini revision -m "Add inscription materialized view"
    ```
   
   This will create a new migration script in the `db/migrations/versions` directory.
   The script will contain DDL statement examples that you can use as a reference.
3. Write the migration script. See the recommendations below
   in [Writing migrations](#writing-migrations).
4. Update schema DDL in `db/migrations/schema.sql` to reflect the new database state after
   the migration. This file is used for a reference only, for example, to see how the migration
   changes the database schema. This is helpful on code review.

   <br>

   Run the following command with a URL to a test Clickhouse instance. This will not modify any
   existing database objects and will clean up after itself (hopefully).

   ```bash
   CLICKHOUSE_URL="clickhouse+native://default:@localhost" python db/migrations/dump_schema.py
   ```
5. Run pytest to test the migrations.

## Writing migrations

* Do not ever modify the migration scripts that have already been merged to master branch.
* Migrations should be backward compatible. This means that the migration should be compatible
  with the previous app version that is already deployed to production. For example, if you add a
  new column to a table, the app code should not break if it does not use the new column. But if
  you rename a column, which is used by the app, the app will break.
* Do not place database name in the DDL statements. The database name should be implicitly
  inferred from the connection URL.
* Do not use `IF EXISTS` or `IF NOT EXISTS` in the DDL statements. This can lead to unexpected
  database state.
* Do not use `USE` statement in the migration scripts.
* Avoid long-running operations in the migration scripts.
* If you need to perform some long-running data transformation, consider doing DDL-only via
  the migration script and deploy a special worker to perform the data transformation.

## Deploying migrations manually

* Show current revision in the database

    ```bash
    CLICKHOUSE_URL="clickhouse+native://user:password@host:9000/db" alembic current
    ```
* Deploy the latest migrations

    ```bash
    CLICKHOUSE_URL="clickhouse+native://user:password@host:9000/db" alembic upgrade head
    ````

* Rollback the latest migration

    ```bash
    CLICKHOUSE_URL="clickhouse+native://user:password@host:9000/db" alembic downgrade -1
    ```

## Troubleshooting

* If you get an error during the migration, you'll have to manually fix the database state.
  Use Alembic's option `--sql` (aka offline mode) to generate the SQL script that would be executed
  by Alembic.
  
  ```bash
  alembic upgrade --sql head  # show all migrations sql from the beginning
  alembic upgrade --sql <from_revision>:<to_revision>  # shows migrations sql in the given revision range
  ```

* Dump schema of any Clickhouse database to stdout (useful for comparing schemas with the schema file `db/migrations/schema.sql`):

  ```sql
  python ethereumetl/scripts/dump_schema_ddl.py -u clickhouse://user:password@host:9000/db
  ```


### Hacks

* Use `CLICKHOUSE_REPLICATED=1` env var to assume a replicated clickhouse instance when
  generating the schema DDL in offline (`--sql`) mode.

## Example: changing primary key order of a MergeTree table

Suppose we have a table `blocks` with the following schema:

```sql
CREATE TABLE blocks (
    block_id UInt64,
    block_hash String,
)
ENGINE = MergeTree()
ORDER BY block_id
```

And we want to change the primary key order to `ORDER BY block_hash`. And we want to do this
without the table users noticing any downtime.

### 1. 1st Schema Migration (DDL, fast)

1. **Create New Table**:  
   Make a new table with the desired `ORDER BY` clause.

    ```sql
    CREATE TABLE blocks_new (
        block_id UInt64,
        block_hash String,
    )
    ENGINE = MergeTree()
    ORDER BY block_hash
    ```

2. **Materialized View**:  
   Set up a materialized view to copy new data from the old table to the new table.

    ```sql
    CREATE MATERIALIZED VIEW blocks_mv TO blocks_new AS
    SELECT *
    FROM blocks
    ```

### 2. Data Migration (DML, long-running)

Prepare and run a script to copy old data from the old table to the new table.

```sql
INSERT INTO blocks_new
SELECT *
FROM blocks
WHERE block_id NOT IN (
    SELECT block_id
    FROM blocks_new
)
```

### 3. 2nd Schema Migration (DDL, fast)

1. Make sure that the data migration script has finished successfully.
2. **Table Swap**:  
   Use `EXCHANGE TABLES` to swap the old and new tables.

    ```sql
    EXCHANGE TABLES blocks AND blocks_new
    ```

   After this step, the old table will be named `blocks_new` and the new table will be
   named `blocks`.
   The `blocks` table will have the desired primary key order and will contain both the data
   before the 1st migration step and the new data which was copied by the materialized view.

3. **Cleanup**:
   Drop the materialized view and the old table (which is now
   named `blocks_new`).

    ```sql
    DROP MATERIALIZED VIEW blocks_mv;
    DROP TABLE blocks_new; 
    ```
