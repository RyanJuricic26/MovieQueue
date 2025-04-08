# ===============================
# ETL Configuration for MovieQueue
# ===============================

# Batch size for Neo4j inserts
BATCH_SIZE = 100

# Top-K movies to select per genre
TOP_K = 250

# Input file paths
MOVIE_DATA_PATH = "Data/Raw Data/title.basics.tsv"
RATINGS_DATA_PATH = "Data/Raw Data/title.ratings.tsv"
PEOPLE_DATA_PATH = "Data/Raw Data/name.basics.tsv"
PRINCIPALS_DATA_PATH = "Data/Raw Data/title.principals.tsv"

# Output directory for generated relationships
REL_OUTPUT_DIR = "Data/Relationships"
