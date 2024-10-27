CREATE TABLE IF NOT EXISTS raw_data.races_raw_data (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  hippodrome VARCHAR(100) NOT NULL,
  pmu_num VARCHAR(10) NOT NULL,
  race_json JSONB NOT NULL
);
