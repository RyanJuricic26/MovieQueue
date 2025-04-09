# MovieQueue ETL Pipeline

This ETL script loads movie, people, and relationship data into the MovieQueue Neo4j database.

---

## ✅ What it does

1. Filters the top **250 movies per genre** (including "Adult" treated as a genre)
2. Automatically creates:
   - Movie nodes with genre relationships
   - People nodes linked only to the filtered movies
   - People -> Movie Relationships (`[r:ACTED_IN]`, `[r:DIRECTED]`, etc.)
   - Loads these relationships into the Neo4j graph
3. Single-command ETL pipeline
4. Displays terminal progress with `tqdm`

---

## 📂 Required Input Files (in `/Data/Raw Data/`):

- `title.basics.tsv`
- `title.ratings.tsv`
- `title.principals.tsv`
- `name.basics.tsv`

---

## 🟣 How to run

```bash
# From the project root directory
python -m ETL.MovieQueueETL
```

---

## 🟣 Notes

- All relationships are dervied from the principals dataset, specifically the job and category columns
- Top movies are selected based on `numVotes`
- `isAdult=1` is treated as an additional genre labeled `Adult`

---

## ⚙️ Configuration

Configuration has been moved to `etl_config.py`.

Ex: 
```python
BATCH_SIZE = 100
TOP_K = 250
```

---

## ✅ Dependencies

- pandas
- tqdm
- neo4j-driver

Make sure your virtual environment has them installed:

```bash
pip install pandas tqdm neo4j
```

---

## 👀 Output Example

- There is no output file, the output is the data being loaded into the Graph Database.

---
