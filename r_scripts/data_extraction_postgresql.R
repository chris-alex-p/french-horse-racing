library(RPostgres)

# set working directory to directory of script
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))
getwd()

# Load database connection details from environment variables
host <- Sys.getenv("DB_HOST")
port <- Sys.getenv("DB_PORT")
db_name <- Sys.getenv("DB_NAME")
username <- Sys.getenv("DB_USER")
password <- Sys.getenv("DB_PASSWORD")

# Check if all credentials are set
if (is.null(host) | is.null(port) | is.null(db_name) | 
    is.null(username) | is.null(password)) {
  stop("Error: Please set all database environment variables!")
}

# Connect to PostgreSQL database
connection <- dbConnect(
  Postgres(), 
  host = host, port = port, dbname = db_name, 
  user = username, password = password
)

# Path to SQL file consisting of query
sql_file_path <- paste0(
  "../sql_scripts/queries/french_trotting_2023_analysis_data_extraction.sql" 
)

# Read SQL query from file. 
sql <- readLines(sql_file_path, warn = FALSE)  
sql <- paste(sql, collapse = "\n")

# Execute the query and store results in a data frame
data <- dbGetQuery(connection, sql)

# Close the connection
dbDisconnect(connection)

# Print a message to confirm data extraction
cat("Data extraction complete! ", nrow(data), " rows retrieved.")

# Save the data frame as a CSV file for further analysis
file_path <- "../data/french_trotting_2023_raw_data.csv"
write.csv(data, file = file_path, row.names = FALSE, fileEncoding = 'utf-8')