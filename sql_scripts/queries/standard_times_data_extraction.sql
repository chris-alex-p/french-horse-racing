SELECT 
  r.race_json -> 'reunion' ->> 'date_reunion' AS date_reunion,
  --r.race_json -> 'reunion' -> 'hippodrome' ->> 'country_code' AS country_code,
  r.race_json -> 'reunion' -> 'hippodrome' ->> 'name' AS hippodrome,
  r.race_json ->> 'lib_piste_course' AS piste_course,
  r.race_json ->> 'num_course_pmu' AS num_course_pmu,
  r.race_json ->> 'discipline' AS discipline, 
  r.race_json ->> 'distance' AS distance,
  r.race_json ->> 'typ_dep_course' AS depart,
  r.race_json ->> 'lib_parcours_course' AS parcours_course,
  r.race_json ->> 'type_course' AS type_course,
  r.race_json ->> 'categ_course' AS categ_course,
  r.race_json ->> 'montant_total_allocation' AS total_allocation,
  j -> 'cheval' ->> 'nom_cheval' AS nom_cheval,
  j -> 'monte' ->> 'nom_monte' AS nom_driver,
  j -> 'reduction_km' AS reduction_km,
  j ->> 'texte_place_arrivee' AS texte_place_arrivee
FROM raw_data.races_raw_data AS r
CROSS JOIN jsonb_array_elements((r.race_json ->> 'partants')::jsonb) AS j
WHERE r.race_json ->> 'discipline' IN ('Attelé', 'Monté')
  AND j ->> 'texte_place_arrivee' = '01'
  AND r.race_json -> 'reunion' -> 'hippodrome' ->> 'country_code' = 'FRA'
  AND r.race_json -> 'reunion' ->> 'date_reunion' LIKE '2023%'; 