-- ...

TRUNCATE shared_poi;
INSERT INTO shared_poi SELECT * FROM view_shared_poi;
VACUUM ANALYZE shared_poi;
