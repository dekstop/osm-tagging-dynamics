-- http://wiki.postgresql.org/wiki/Aggregate_Median

CREATE OR REPLACE FUNCTION _final_median(numeric[])
   RETURNS numeric AS
$$
   SELECT AVG(val)
   FROM (
     SELECT val
     FROM unnest($1) val
     ORDER BY 1
     LIMIT  2 - MOD(array_upper($1, 1), 2)
     OFFSET CEIL(array_upper($1, 1) / 2.0) - 1
   ) sub;
$$
LANGUAGE 'sql' IMMUTABLE;
 
CREATE AGGREGATE median(numeric) (
  SFUNC=array_append,
  STYPE=numeric[],
  FINALFUNC=_final_median,
  INITCOND='{}'
);


-- http://stackoverflow.com/a/14309370
-- Usage: SELECT percentile_cont(array_agg(my_sort_column), 0.25) as my_result_column FROM ...

CREATE OR REPLACE FUNCTION array_sort (ANYARRAY)
RETURNS ANYARRAY LANGUAGE SQL
AS $$
  SELECT ARRAY(
      SELECT $1[s.i] AS "foo"
      FROM
          generate_series(array_lower($1,1), array_upper($1,1)) AS s(i)
      ORDER BY foo
  );
$$;

CREATE OR REPLACE FUNCTION percentile_cont(myarray real[], percentile real)
  RETURNS real AS
$$
  DECLARE
    ary_cnt INTEGER;
    row_num real;
    crn real;
    frn real;
    calc_result real;
    new_array real[];
  BEGIN
    ary_cnt = array_length(myarray,1);
    row_num = 1 + ( percentile * ( ary_cnt - 1 ));
    new_array = array_sort(myarray);

    crn = ceiling(row_num);
    frn = floor(row_num);

    if crn = frn and frn = row_num then
      calc_result = new_array[row_num];
    else
      calc_result = (crn - row_num) * new_array[frn] 
              + (row_num - frn) * new_array[crn];
    end if;

    RETURN calc_result;
  END;
$$
LANGUAGE 'plpgsql' IMMUTABLE;