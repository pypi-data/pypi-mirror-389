WITH regional_sales AS (
    SELECT region, SUM(amount) AS total_sales
    FROM orders_cte
    GROUP BY region
    INTERSECT
    SELECT region, SUM(amount) AS total_sales
    FROM another_schema.orders_cte
    GROUP BY region
)
, top_regions AS (
    SELECT region
    FROM regional_sales
    WHERE total_sales > (SELECT SUM(total_sales)/10 FROM regional_sales)
)
SELECT region,
       "ts"."product" as prod,
       SUM(schema.table.quantity) AS product_units,
FROM "miedema"."store", regional_sales rs, regional_sales
JOIN t2 ON orders.id = t2.id
JOIN t3 USING (id)
WHERE region IN (SELECT region FROM top_regions)
HAVING SUM(amount) > 1000
