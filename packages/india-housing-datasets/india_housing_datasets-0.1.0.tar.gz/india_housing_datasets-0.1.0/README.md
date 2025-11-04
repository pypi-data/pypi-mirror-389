# 🏠 India Housing Datasets

A lightweight Python library that provides clean housing datasets for major Indian cities — **Ahmedabad**, **Gurugram**, and **Mumbai** — in `sklearn` style.

## Installation
```bash
pip install india_housing_datasets

🚀 Quick Example
from india_housing_datasets import fetch_ahmedabad_housing

dataset = fetch_ahmedabad_housing()
print(dataset["data"].head())
print(dataset["target"].head())
print(dataset["DESCR"])

🏙️ Included Datasets
| City          | Function                    | Description                         |
| ------------  | --------------------------- | ----------------------------------- |
| 🏡 Ahmedabad | fetch_ahmedabad_housing()  | Prices, BHK, area, floor, location  |
| 🏙️ Gurugram  | fetch_gurugram_housing()    | Modern housing and real-estate data |
| 🌆 Mumbai    | fetch_mumbai_housing()     | Urban apartment data for analysis   |

💡 Author

Vishal Baghel
📧 baghelvishal264@gmail.com

🌐 GitHub Repository

📜 License

MIT License © 2025 — Vishal Baghel
----
