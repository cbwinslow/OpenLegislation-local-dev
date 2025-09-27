# SQL Data Model

This document outlines the proposed SQL data model for the OpenLegislation project, designed to be compatible with both the existing NYS Senate data and the new `govinfo.gov` data. The model is designed for PostgreSQL and includes support for `pgvector` for text embeddings.

## Table of Contents

- [Schema Diagram](#schema-diagram)
- [Tables](#tables)
  - [bills](#bills)
  - [amendments](#amendments)
  - [actions](#actions)
  - [sponsors](#sponsors)
  - [bill_sponsors](#bill_sponsors)
  - [committees](#committees)
  - [bill_committees](#bill_committees)
  - [votes](#votes)
  - [related_bills](#related_bills)
  - [laws](#laws)
  - [govinfo_metadata](#govinfo_metadata)
- [Views](#views)
- [Triggers](#triggers)
- [Indexes](#indexes)

## Schema Diagram

(A schema diagram will be generated once the table structure is finalized.)

## Tables

### `bills`

Stores the core information for each legislative bill.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each bill. |
| `base_bill_id` | `VARCHAR(255)` | `UNIQUE NOT NULL` | The base identifier for the bill (e.g., "S1234"). |
| `session_year` | `INTEGER` | `NOT NULL` | The legislative session year. |
| `title` | `TEXT` | | The official title of the bill. |
| `summary` | `TEXT` | | A summary of the bill's content. |
| `status` | `VARCHAR(255)` | | The current status of the bill. |
| `ldblurb` | `TEXT` | | The LDBlurb field from the existing data model. |
| `substituted_by` | `VARCHAR(255)` | | The base bill ID of the bill that substituted this one. |
| `reprint_of` | `VARCHAR(255)` | | The bill ID of the bill this is a reprint of. |
| `direct_previous_version` | `VARCHAR(255)` | | The bill ID of the direct previous version of this bill. |
| `chapter_num` | `INTEGER` | | The chapter number if the bill becomes law. |
| `chapter_year` | `INTEGER` | | The year the bill was signed into law. |
| `federal_congress` | `INTEGER` | | The federal congress number for federal bills. |
| `federal_source` | `VARCHAR(255)` | | The source of the federal data (e.g., "govinfo"). |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |
| `updated_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was last updated. |

### `amendments`

Stores the different versions (amendments) of each bill.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each amendment. |
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `version` | `VARCHAR(10)` | `NOT NULL` | The amendment version (e.g., "A", "B"). |
| `memo` | `TEXT` | | The memo for the amendment. |
| `law_section` | `VARCHAR(255)` | | The section of the law the amendment affects. |
| `law_code` | `VARCHAR(255)` | | The law code of the amendment. |
| `act_clause` | `TEXT` | | The "AN ACT TO..." clause of the amendment. |
| `full_text` | `TEXT` | | The full text of the amendment. |
| `stricken` | `BOOLEAN` | `DEFAULT FALSE` | A flag marking the amendment as stricken. |
| `uni_bill` | `BOOLEAN` | `DEFAULT FALSE` | A flag marking the amendment as a uni-bill. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |
| `updated_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was last updated. |

### `actions`

Stores the legislative actions taken on each bill.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each action. |
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `action_date` | `DATE` | `NOT NULL` | The date the action was performed. |
| `chamber` | `VARCHAR(50)` | | The chamber in which the action occurred. |
| `sequence_no` | `INTEGER` | | The sequence number for ordering actions. |
| `text` | `TEXT` | | The text of the action. |
| `type` | `VARCHAR(255)` | | The type of action. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |

### `sponsors`

Stores information about bill sponsors.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each sponsor. |
| `member_id` | `VARCHAR(255)` | `UNIQUE` | The unique identifier for the legislative member. |
| `full_name` | `VARCHAR(255)` | | The full name of the sponsor. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |

### `bill_sponsors`

A join table for the many-to-many relationship between bills and sponsors.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `sponsor_id` | `INTEGER` | `REFERENCES sponsors(id)` | Foreign key to the `sponsors` table. |
| `is_primary` | `BOOLEAN` | `DEFAULT TRUE` | A flag to indicate if this is the primary sponsor. |

### `committees`

Stores information about legislative committees.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each committee. |
| `committee_id` | `VARCHAR(255)` | `UNIQUE` | The unique identifier for the committee. |
| `name` | `VARCHAR(255)` | | The name of the committee. |
| `chamber` | `VARCHAR(50)` | | The chamber the committee belongs to. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |

### `bill_committees`

A join table for the many-to-many relationship between bills and committees.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `committee_id` | `INTEGER` | `REFERENCES committees(id)` | Foreign key to the `committees` table. |

### `votes`

Stores the results of votes on each bill.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each vote. |
| `amendment_id` | `INTEGER` | `REFERENCES amendments(id)` | Foreign key to the `amendments` table. |
| `vote_date` | `TIMESTAMP` | | The date and time of the vote. |
| `vote_type` | `VARCHAR(255)` | | The type of vote (e.g., "Yea-Nay"). |
| `ayes` | `INTEGER` | | The number of "aye" votes. |
| `nays` | `INTEGER` | | The number of "nay" votes. |
| `abstains` | `INTEGER` | | The number of abstentions. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |

### `related_bills`

Stores relationships between bills.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `related_bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the related bill. |
| `relationship_type` | `VARCHAR(255)` | | The type of relationship (e.g., "same-as"). |

### `laws`

Stores information about bills that have become law.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier for each law. |
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `law_type` | `VARCHAR(255)` | | The type of law (e.g., "Public Law"). |
| `law_number` | `VARCHAR(255)` | | The official law number. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |

### `govinfo_metadata`

Stores metadata specific to `govinfo.gov` data.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `bill_id` | `INTEGER` | `REFERENCES bills(id)` | Foreign key to the `bills` table. |
| `package_id` | `VARCHAR(255)` | | The `govinfo.gov` package ID. |
| `last_modified` | `TIMESTAMP` | | The last modified timestamp from `govinfo.gov`. |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | The timestamp when the record was created. |

## Views

The following views are created in the `V2__create_views_and_triggers.sql` migration script:

- `bills_with_sponsors`: A view that joins the `bills` and `sponsors` tables to provide a list of bills with their primary sponsors.
- `latest_amendments`: A view that shows the most recent amendment for each bill.

## Triggers

The following triggers are created in the `V2__create_views_and_triggers.sql` migration script:

- `update_bills_updated_at`: A trigger that automatically updates the `updated_at` timestamp on the `bills` table whenever a record is updated.
- `update_amendments_updated_at`: A trigger that automatically updates the `updated_at` timestamp on the `amendments` table whenever a record is updated.

## Indexes

Indexes are created on all foreign key columns to improve the performance of join operations. See the `V2__create_views_and_triggers.sql` migration script for a complete list of indexes.

## Example Queries

This section provides a few example queries to demonstrate how to interact with the database.

### Find a Bill by its Base ID

This query retrieves a bill and its primary sponsor using the `bills_with_sponsors` view.

```sql
SELECT
    base_bill_id,
    title,
    sponsor_name
FROM
    bills_with_sponsors
WHERE
    base_bill_id = 'S1234';
```

### Find the Latest Version of a Bill

This query retrieves the latest amendment for a specific bill using the `latest_amendments` view.

```sql
SELECT
    b.base_bill_id,
    la.version,
    la.full_text
FROM
    bills b
JOIN
    latest_amendments la ON b.id = la.bill_id
WHERE
    b.base_bill_id = 'S1234';
```
