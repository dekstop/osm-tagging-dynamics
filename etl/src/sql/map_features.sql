-- based on http://wiki.openstreetmap.org/wiki/Map_Features

DROP TABLE IF EXISTS map_features;
DROP TYPE IF EXISTS map_feature_type;

CREATE TYPE map_feature_type AS ENUM ('primary', 'other');

CREATE TABLE map_features (
  key       TEXT NOT NULL,
  type      map_feature_type NOT NULL DEFAULT 'other'
);
CREATE UNIQUE INDEX idx_map_features_key ON map_features(key);

INSERT INTO map_features(key, type) VALUES
  ('abandoned', 'other'),
  ('abutters', 'other'),
  ('access', 'other'),
  ('addr', 'other'),
  ('addr:city', 'other'),
  ('addr:country', 'other'),
  ('addr:district', 'other'),
  ('addr:full', 'other'),
  ('addr:hamlet', 'other'),
  ('addr:housename', 'other'),
  ('addr:housenumber', 'other'),
  ('addr:interpolation', 'other'),
  ('addr:place', 'other'),
  ('addr:postcode', 'other'),
  ('addr:province', 'other'),
  ('addr:state', 'other'),
  ('addr:street', 'other'),
  ('addr:subdistrict', 'other'),
  ('addr:suburb', 'other'),
  ('admin_level', 'other'),
  ('aerialway', 'primary'),
  ('aeroway', 'primary'),
  ('amenity', 'primary'),
  ('area', 'other'),
  ('attribution', 'other'),
  ('atv', 'other'),
  ('barrier', 'primary'),
  ('basin', 'other'),
  ('bicycle', 'other'),
  ('border_type', 'other'),
  ('boundary', 'primary'),
  ('bridge', 'other'),
  ('building', 'primary'),
  ('building:fireproof', 'other'),
  ('building:levels', 'other'),
  ('cables', 'other'),
  ('circuits', 'other'),
  ('communication:mobile_phone', 'other'),
  ('construction', 'other'),
  ('contact', 'other'),
  ('contact:fax', 'other'),
  ('contact:phone', 'other'),
  ('covered', 'other'),
  ('craft', 'primary'),
  ('crossing', 'other'),
  ('cuisine', 'other'),
  ('cutting', 'other'),
  ('cycleway', 'primary'),
  ('denomination', 'other'),
  ('description', 'other'),
  ('diet', 'other'),
  ('direction', 'other'),
  ('disused', 'other'),
  ('drive_in', 'other'),
  ('drive_through', 'other'),
  ('ele', 'other'),
  ('electrified', 'other'),
  ('email', 'other'),
  ('embankment', 'other'),
  ('emergency', 'primary'),
  ('end_date', 'other'),
  ('entrance', 'other'),
  ('est_width', 'other'),
  ('fax', 'other'),
  ('fence_type', 'other'),
  ('fixme', 'other'),
  ('foot', 'other'),
  ('ford', 'other'),
  ('frequency', 'other'),
  ('fuel', 'other'),
  ('gauge', 'other'),
  ('generator:method', 'other'),
  ('generator:output', 'other'),
  ('generator:source', 'other'),
  ('geological', 'primary'),
  ('hazmat', 'other'),
  ('height', 'other'),
  ('highway', 'primary'),
  ('historic', 'primary'),
  ('horse', 'other'),
  ('iata', 'other'),
  ('icao', 'other'),
  ('image', 'other'),
  ('incline', 'other'),
  ('industrial', 'other'),
  ('information', 'other'),
  ('intermittent', 'other'),
  ('internet_access', 'other'),
  ('is_in', 'other'),
  ('is_in:city', 'other'),
  ('is_in:country', 'other'),
  ('junction', 'other'),
  ('landuse', 'primary'),
  ('lanes', 'other'),
  ('layer', 'other'),
  ('leisure', 'primary'),
  ('lit', 'other'),
  ('location', 'other'),
  ('lock', 'other'),
  ('man_made', 'primary'),
  ('material', 'other'),
  ('maxheight', 'other'),
  ('maxlength', 'other'),
  ('maxspeed', 'other'),
  ('maxstay', 'other'),
  ('maxweight', 'other'),
  ('maxwidth', 'other'),
  ('military', 'other'),
  ('minspeed', 'other'),
  ('mooring', 'other'),
  ('motorroad', 'other'),
  ('mountain_pass', 'other'),
  ('mtb:description', 'other'),
  ('mtb_scale', 'other'),
  ('name', 'other'),
  ('narrow', 'other'),
  ('natural', 'primary'),
  ('noexit', 'other'),
  ('note', 'other'),
  ('office', 'primary'),
  ('official_name', 'other'),
  ('oneway', 'other'),
  ('opening_hours', 'other'),
  ('operator', 'other'),
  ('organic', 'other'),
  ('overtaking', 'other'),
  ('passing_places', 'other'),
  ('phone', 'other'),
  ('place', 'primary'),
  ('population', 'other'),
  ('power', 'primary'),
  ('proposed', 'other'),
  ('protected_area', 'other'),
  ('psv', 'other'),
  ('public_transport', 'primary'),
  ('railway', 'primary'),
  ('recycling_type', 'other'),
  ('ref', 'other'),
  ('primary', 'other'),
  ('primary_point', 'other'),
  ('religion', 'other'),
  ('route', 'primary'),
  ('ruins', 'other'),
  ('sac_scale', 'other'),
  ('service', 'other'),
  ('shelter_type', 'other'),
  ('shop', 'primary'),
  ('site', 'other'),
  ('social_facility', 'other'),
  ('source', 'other'),
  ('sport', 'primary'),
  ('start_date', 'other'),
  ('step_count', 'other'),
  ('surface', 'other'),
  ('tactile_paving', 'other'),
  ('TMC:LocationCode', 'other'),
  ('toilets:wheelchair', 'other'),
  ('tourism', 'primary'),
  ('tower:type', 'other'),
  ('tracks', 'other'),
  ('tracktype', 'other'),
  ('traffic_calming', 'other'),
  ('traffic_sign', 'other'),
  ('trail_visibility', 'other'),
  ('tunnel', 'other'),
  ('type', 'other'),
  ('url', 'other'),
  ('usage', 'other'),
  ('vending', 'other'),
  ('voltage', 'other'),
  ('water', 'other'),
  ('waterway', 'primary'),
  ('website', 'other'),
  ('wheelchair', 'other'),
  ('width', 'other'),
  ('wikipedia', 'other'),
  ('winter_road', 'other'),
  ('wires', 'other'),
  ('wood', 'other');
