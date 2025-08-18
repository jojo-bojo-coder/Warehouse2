LOAD DATABASE
    FROM 'sqlite://db.sqlite3'
    INTO postgresql://nagham:1234@localhost/warehouse

WITH include no drop, truncate, create no tables, create no indexes, reset sequences

SET work_mem to '16MB', maintenance_work_mem to '512 MB';