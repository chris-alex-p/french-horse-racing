# Load packages
library(tidyverse)

# Import data
data <- read.csv(
  "../data/french_trotting_2023_raw_data.csv", encoding = "utf-8"
)

glimpse(data)

summary(data)

str(data)

# Counting NAs for all columns
sapply(data, function(x) sum(is.na(x)))

# hippodrome column trim?
begin_space_hippodrome <- data %>% 
  filter(grepl("^ .*", hippodrome))
end_space_hippodrome <- data %>% 
  filter(grepl(".* $", hippodrome))
double_whitespace_hippodrome <- data %>% 
  filter(grepl("  ", hippodrome))
data$hippodrome <- str_squish(data$hippodrome)
remove(list = setdiff(ls(), "data"))

# Reason for NAs in piste_course column?
na_piste_course_hippodromes <- data %>% 
  filter(is.na(piste_course)) %>% 
  select(hippodrome) %>% 
  distinct() %>% 
  pull()
sort(na_piste_course_hippodromes)
# Hippodrome de Casatorra: 
# Piste : 1.060 mètres environ (herbe) Corde à droite
data$piste_course <- ifelse(
  data$hippodrome == "BIGUGLIA(Casatorra)", "Herbe", data$piste_course
)
# Hippodrome de Marchès in Castelsarrasin
# Piste : 1.060 mètres environ (sable) Corde à droite
data$piste_course <- ifelse(
  data$hippodrome == "CASTELSARRASIN", "Sable", data$piste_course
)


# NAs in 'depart': replacing missing values
data$depart <- ifelse(is.na(data$depart), "Départ Volté", data$depart)


# There are a lot of NAs in the parcours_course column. But we will leave them 
# as is, because this column is only of interest for races run in Vincennes.


# Replace NAs in type_course if sensible
# These are all possible race types in french trotting at the moment:
course_types <- c(
  "Groupe I", "Groupe II", "Groupe III", "Course A", "Course B", "Course C", 
  "Course D", "Course E", "Course F", "Course G", "Course H", "Course R"
)
# Constructing a pattern to use with str_extract on the conditions_txt_course
# column with the goal of extracting the type of the race from the conditions 
# text.
course_types_pattern <- paste(
  c(
    "Groupe I*", "Course A", "Course B", "Course C", "Course D", 
    "Course E", "Course F", "Course G", "Course H", "Course R"
  ),
  collapse = "|"
)
# New column type_course_modified.
data$type_course_modified <- ifelse(
  is.na(data$type_course) | (! data$type_course %in% course_types),
  str_extract(data$conditions_txt_course, course_types_pattern),
  data$type_course
)
# # There are still 135 missing values in the course_type column. Actually those
# # are all participants of races run in Martinique. Since we are only interested 
# # in mainland France and the horse populations don't mix, those observations 
# # will be dropped also.
# data_no_type_course <- data %>% 
#   filter(is.na(type_course_modified))
# data <- data %>%
#   filter(!is.na(type_course_modified))



# Using the categ_course column to mark observations from amateur races or 
# apprentice races.
# Add column to mark amateur races:
race_categories <- sort(unique(data$categ_course))
race_categories
am_race_categories <- race_categories[grepl('AMATEUR', race_categories)]
am_race_categories
setdiff(race_categories, am_race_categories)
data$am_course <- data$categ_course %in% am_race_categories
# Add column to mark apprentice races:
# add lads column
lads_race_categories <- race_categories[grepl('LADS|ALJ', race_categories)]
lads_race_categories
setdiff(race_categories, lads_race_categories)
data$lads_course <- data$categ_course %in% lads_race_categories
# Checking if there are any other lads or am races
# lads races
data$lads_race <- grepl('lads', data$conditions_txt_course, ignore.case = TRUE)
discrepancies <- data %>% 
  filter(lads_course != lads_race)
# After taking a closer look at the conditions_txt_course for the five races 
# where discrepancies have been detected only one of those five races is really
# a lads race.
data$lads_course <- ifelse(
  data$date_reunion == '2023-04-02' & 
    data$hippodrome == 'NIMES(Les Courbiers)' & data$num_course_pmu == 5,
  TRUE,
  data$lads_course
)
# am races
data$am_race <- grepl('amateur', data$conditions_txt_course, ignore.case = TRUE)
discrepancies <- data %>% 
  filter(am_course != am_race)
# no discrepancies with amateur races
# removing lads_race and am_race from df
data <- data %>% 
  select(-c(lads_race, am_race))


# add total_allocation_eur column
data <- data %>% 
  mutate(
    total_allocation_eur = as.integer(gsub('\\.| euros', '', total_allocation))
  )


# Réduction kilometrique measured in seconds
# Search for unplausible réduction kilométrique data.
data_unusual_reduction_km <- data %>% 
  filter(
    !grepl("\\\"1'[0-9]{2}\\\\\\\"[0-9]{2}\\\"", reduction_km), 
    !is.na(reduction_km)
  )
# For now we are going to set these reduction_km which seem unplausible to NA
data$reduction_km <- ifelse(
  !grepl("\\\"1'[0-9]{2}\\\\\\\"[0-9]{2}\\\"", data$reduction_km),
  NA,
  data$reduction_km
)
# Transform réduction kilométrique (red km) from string to red km measured in
# seconds
data <- data %>% 
  mutate(
    red_km_sec = as.numeric(substr(reduction_km, 2, 2)) * 60 +
      as.numeric(substr(reduction_km, 4, 5)) + 
      ( as.numeric(substr(reduction_km, 8, 9)) / 100 )
  )


# texte_place_arrivee
sort(unique(data$texte_place_arrivee))
data_unusual_texte_place_arrivee <- data %>% 
  filter(str_length(texte_place_arrivee) > 2)
# Possible values for string values in texte_place_arrivee:
string_arrivee <- data %>% 
  filter(grepl("^[A-Z]", texte_place_arrivee, ignore.case = TRUE)) %>% 
  select(texte_place_arrivee) %>% 
  distinct() %>% 
  pull()
string_arrivee
# Create new columns with dummy variables for each case when the horse did not
# finish the race
data <- data %>%
  mutate(
    # Disqualifications
    disqualifie = ifelse(texte_place_arrivee == "Disqualifié", 1, 0),
    # Horses who were signed up for this race but didn't partake
    non_partant = ifelse(texte_place_arrivee == "Non Partant", 1, 0),
    # Stopped in mid race
    arrete = ifelse(texte_place_arrivee == "Arrêté", 1, 0),
    # Very long distance between horse and winner
    distancie = ifelse(texte_place_arrivee == "Distancé", 1, 0),
    # Horse who have fallen or have crashed
    tombe = ifelse(texte_place_arrivee == "Tombé", 1, 0),
    # Didn't run when was started
    reste_poteau = ifelse(texte_place_arrivee == "Resté au poteau", 1, 0),
    # Quite similar to Tombé
    derobe = ifelse(texte_place_arrivee == "Dérobé", 1, 0)
  )

# num_place_arrivee
sort(unique(data$num_place_arrivee))
# Create dummy variable for 'Non partant'
data$non_partant <- ifelse(data$num_place_arrivee == "Non partant", 1, 0)
data$non_partant <- ifelse(is.na(data$non_partant), 0, data$non_partant)
sum(data$non_partant)
sum(is.na(data$num_place_arrivee))
# New variable for finishing position: fin_pos
data$fin_pos <- as.integer(data$num_place_arrivee)
sum(is.na(data$fin_pos))

data_first_place <- data %>% 
  filter(texte_place_arrivee == "01" | num_place_arrivee == "01")
unique(data_first_place$texte_place_arrivee)
possible_dead_heats <- data_first_place %>% 
  group_by(date_reunion, hippodrome, num_course_pmu) %>% 
  summarise(n = n()) %>% 
  arrange(desc(n), date_reunion)


# Write prepared data to csv file
write.csv(
  data, "../data/french_trotting_2023_analysis_data.csv", row.names = FALSE,
  fileEncoding = "utf-8"
)