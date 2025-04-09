# 🎬 MovieQueue Data Directory

This folder contains raw and preprocessed data used by the MovieQueue app.  
All datasets included here originate from [IMDb's Non-Commercial Datasets](https://developer.imdb.com/non-commercial-datasets/).

---

## 📚 Data Source

All data is sourced from:

> 📎 [IMDb Non-Commercial Datasets](https://developer.imdb.com/non-commercial-datasets/)  
> © IMDb.com, Inc. Licensed under [IMDb’s Non-Commercial Data License](https://developer.imdb.com/non-commercial-datasets/#license)

---

## ⚠️ Usage Disclaimer

The datasets provided here are:

- **For personal, academic, and non-commercial use only**
- Distributed as-is under IMDb’s [non-commercial license terms](https://developer.imdb.com/non-commercial-datasets/#license)
- Not to be used in any commercial product or for-profit application

Please refer to IMDb’s official licensing documentation for full terms.

---

## 📝 Included Files

This directory typically contains:

- `name.basics.tsv` – Actor, director, writer metadata
- `title.basics.tsv` – Title, genre, and metadata
- `title.crew.tsv` – Director, Writer, etc. connections
- `title.episode.tsv` – TV episode details
- `title.principals.tsv` – Cast and crew links
- `title.ratings.tsv` – IMDb ratings data
- `title.akas.tsv` – Alternate titles and translations

Note: File presence may vary depending on your use case or preprocessing steps.

---

## 📦 How This Data Is Used in MovieQueue

The IMDb datasets power MovieQueue’s:

- 🎯 Movie recommendation engine
- ⭐ Rating and filtering system
- 🧑 People -> Movie relationships
- 📊 Analytics and personalization features

---

If you have questions about how the data is processed, please refer to the main project’s `ETL/` directory and the documentation in the main [README.md](../README.md).
