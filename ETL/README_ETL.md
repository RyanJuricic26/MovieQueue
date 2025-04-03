# MovieQueue ETL Pipeline

This ETL script loads movie, people, and relationship data into the MovieQueue Neo4j database.

---

## ✅ What it does

1. Filters the top **1000 movies per genre** (including "Adult" treated as a genre)
2. Automatically creates:
   - Movie nodes with genre relationships
   - People nodes linked only to the filtered movies
   - Relationship CSVs (`ACTED_IN.csv`, `DIRECTED.csv`, etc.)
   - Loads these relationships into the Neo4j graph
3. Single-command ETL pipeline
4. Displays terminal progress with `tqdm`

---

## 📂 Required Input Files (in `/Data/Raw Data/`):

- `title.basics.tsv`
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

- All relationship CSVs are automatically generated to `/Data/Relationships/`
- Top movies are selected based on `numVotes`
- `isAdult=1` is treated as an additional genre labeled `Adult`

---

## ⚙️ Configuration

Optional configuration will soon be moved to an `etl_config.py` file.
For now, you can adjust directly inside `etl_full.py`:

```python
BATCH_SIZE = 100
TOP_K = 1000
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

- `/Data/Relationships/ACTED_IN.csv`
- `/Data/Relationships/DIRECTED.csv`
- `/Data/Relationships/EDITED.csv`
- ... (all relationships discovered automatically)

---
