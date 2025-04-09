# ===============================
# ETL Configuration for MovieQueue
# ===============================

# Batch size for Neo4j inserts
BATCH_SIZE = 100

# Top-K movies to select per genre
TOP_K = 250

# Input file paths
MOVIE_DATA_PATH = "Data/title.basics.tsv"
RATINGS_DATA_PATH = "Data/title.ratings.tsv"
PEOPLE_DATA_PATH = "Data/name.basics.tsv"
PRINCIPALS_DATA_PATH = "Data/title.principals.tsv"

# Output directory for generated relationships
REL_OUTPUT_DIR = "Data/Relationships"

# Defining data types
DTYPE_BASICS = {
    'tconst': 'string',
    'titleType': 'category',
    'primaryTitle': 'string',
    'originalTitle': 'string',
    'isAdult': 'Int8',
    'startYear': 'string',
    'endYear': 'string',
    'runtimeMinutes': 'string',
    'genres': 'string'
}

DTYPE_RATINGS = {
    'tconst': 'string',
    'averageRating': 'float32',
    'numVotes': 'Int32'
}

DTYPE_NAMES = {
    'nconst': 'string',
    'primaryName': 'string',
    'birthYear': 'string',
    'deathYear': 'string',
    'primaryProfession': 'string',
    'knownForTitles': 'string'
}


DTYPE_PRINCIPALS = {
    'tconst': 'string',
    'ordering': 'Int16',
    'nconst': 'string',
    'category': 'string',
    'job': 'string',
    'characters': 'string'
}

# List of professions to include for relationships
PROFESSION_TO_RELATIONSHIP = {
    "actor": "ACTED_IN",
    "actress": "ACTED_IN",
    "self": "APPEARED_AS_SELF_IN",
    "director": "DIRECTED",
    "producer": "PRODUCED",
    "writer": "WROTE",
    "editor": "EDITED",
    "cinematographer": "SHOT",
    "composer": "COMPOSED_SCORE_FOR",
    "music_department": "CONTRIBUTED_TO_SCORE",
    "music_artist": "CONTRIBUTED_TO_SCORE",
    "soundtrack": "PROVIDED_SOUNDTRACK",
    "animation_department": "ANIMATED",
    "animator": "ANIMATED",
    "art_department": "WORKED_ON_ART",
    "production_designer": "DESIGNED_PRODUCTION",
    "costume_designer": "DESIGNED_COSTUMES",
    "casting_director": "CAST",
    "choreographer": "CHOREOGRAPHED"
}