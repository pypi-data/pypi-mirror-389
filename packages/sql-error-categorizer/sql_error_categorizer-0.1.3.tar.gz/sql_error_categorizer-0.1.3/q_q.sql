select *
from
    store s1,
    store s2
    join store s3
        on s2.store_id = s3.store_id
    join store s4
        on s3.store_id = s4.store_id
where
    s1.store_id > s2.store_id;
