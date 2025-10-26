# Otodom Apartments for Sale – Data Analysis (Q3 2025)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-lightblue)
![Docker](https://img.shields.io/badge/Docker-Compose-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

A **data-driven study of Poznań’s apartment market (Q3 2025)**  
focusing on **price per m²**, **district**, **distance to city centre**, **room count**, and **seller type**.

The project includes a **web-scraper → database pipeline → analysis workflow** with:
- Python + Playwright scraper  
- PostgreSQL ETL pipeline  
- District-level EDA, visualization & regression (OLS & WLS)  
- Model evaluation & residual diagnostics

---

## Key Insights – Q3 2025
> *All numbers based on ~10 pages of Poznań listings scraped in August 2025*

- **Average price/m²:** ≈ **12229.79 PLN/m²** (median ≈ 12264.15 PLN/m²)  
- **Stare Miasto** highest ≈ **14471.59 PLN/m²**, **Nowe Miasto** lowest ≈ **10424.79 PLN/m²**  

--- 

## Project Overview
We scrape apartment listings from [Otodom.pl](https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/wielkopolskie/poznan/poznan/poznan), store them in **PostgreSQL**, and analyze pricing determinants to uncover **spatial & seller-driven pricing patterns**.

---

## Data Pipeline
```mermaid
flowchart TD
    A["Playwright Scraper (scrape_otodom.py)"] --> B["PostgreSQL Database"]
    B --> C["Jupyter Notebook (analyze.ipynb)"]
```

1. **Scraper:** collects ~10 pages of Poznań listings, expands developer group listings  
2. **Database Layer:** SQLAlchemy → PostgreSQL container  
3. **Analysis:** cleaning, `price_per_sqm` feature, district & seller-type EDA, regression  
4. **Containerized:** `docker-compose` orchestrates DB, scraper, Jupyter with `wait-for-it.sh`

---

## Project Structure
```
├── scrape_otodom.py        # Playwright scraper
├── db.py                    # DB helpers (SQLAlchemy)
├── analyze.ipynb            # Cleaning, visualization & regression
├── docker-compose.yml
├── requirements.txt
├── output/                  # csv with data used in the analysis
├── README.md
└── .env / .gitignore / wait-for-it.sh …
```

---

## Analysis Highlights
- **Feature engineering:** `price_per_sqm`, `distance_km` from city centre  
- **District-level stats:** 
- **Seller type analysis:**
- **Regression models:**  
  - OLS on log(price) with `area`, `rooms`, `distance_km`, district dummies  
  - **Weighted Least Squares** to handle heteroskedasticity  
- **Diagnostics:** R², RMSE, residuals vs predicted, residual distribution  

---

## Example Visuals

| |
|-|
|<img width="1005" height="547" alt="image" src="https://github.com/user-attachments/assets/b7b72bae-8956-40e0-b734-82e86274ba81" />
|<img width="1189" height="590" alt="image" src="https://github.com/user-attachments/assets/33f11648-2189-46cd-ba87-0137fe8166e3" />
| |

---

## Key Regression Insights (OLS & WLS & XGBOOST)

We fitted 3 main models to understand price determinants:

| Model       | Dependent Variable | R²    | Key Notes |
|------------|------------------|-------|-----------|
| **OLS**    | `price` (PLN)    | 0.82  | Captures ~82% of price variation; good overall fit. |
| **WLS**    | `log_price`      | 0.95  | Better fit after log-transforming price and applying WLS to handle heteroskedasticity. |
| **XGBoost**| `price` (PLN)    | 0.88  | Tree-based model captures nonlinearities and interactions automatically; strong predictive performance on original price scale (MSE ≈ 4.21e9 PLN²). |


### Important Predictors:
- **Area (m²):** Strong positive influence on price, but with a diminishing return (negative squared-area term).
- **District:** Central areas like **Stare Miasto (+5.0 on log-price)** and **Jeżyce (+1.5)** have substantial premiums over the baseline (Grunwald).
- **Distance to city centre:** Statistically significant, but the sign suggests possible inverse coding or nonlinear effects — interpret cautiously.
- **Weighted Least Squares:** Greatly improved fit (R² from 0.88 → 0.996), reducing heteroskedasticity seen in OLS residuals.


---

## Tools & Skills
- **Python 3.11** – Playwright, BeautifulSoup, Pandas, NumPy, Matplotlib, Seaborn  
- **Statsmodels & scikit-learn** – OLS, WLS, multicollinearity, RESET tests  
- **PostgreSQL + SQLAlchemy** – data storage & ETL  
- **Docker & docker-compose** – containerized pipeline  
- **Jupyter Notebook** – analysis & reporting

---

## License
MIT License – see [LICENSE](LICENSE).

---

## Contact
 **s.abilinska@gmail.com**  
 [LinkedIn – Natalia Bilińska](https://www.linkedin.com/in/natalia-bilińska-8874a3359)

 LinkedIn: [www.linkedin.com/in/natalia-bilińska-8874a3359](https://www.linkedin.com/in/natalia-bilińska-8874a3359)

