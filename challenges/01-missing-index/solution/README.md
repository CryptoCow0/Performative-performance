# Solution: Missing Index

## Basic Fix (passes threshold)

```sql
CREATE INDEX idx_orders_customer_email ON orders(customer_email);
```

## Optimal Fix (covering index, avoids heap lookup)

```sql
CREATE INDEX idx_orders_email_date_covering
ON orders(customer_email, order_date DESC)
INCLUDE (order_id, total_amount, status);
```

The covering index is faster because Postgres can satisfy the entire query
from the index alone (Index Only Scan) without touching the heap pages.

## Why It's Slow Without the Index

- 5M rows, ~2GB table
- Seq Scan reads every page to find matching emails
- Even with parallel seq scan, it takes 15-30s depending on hardware
- With the index: B-tree lookup finds the ~150 matching rows in <1ms
