-- 

TRUNCATE poi_multiple_editors;
INSERT INTO poi_multiple_editors SELECT * FROM view_poi_multiple_editors;
VACUUM ANALYZE poi_multiple_editors;

