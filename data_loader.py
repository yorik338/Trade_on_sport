import pandas as pd

# Список английских лиг
leagues = ["E0", "E1", "E2", "E3"]
base_url = "https://www.football-data.co.uk/mmz4281/2425/"

dataframes = []

for code in leagues:
    url = f"{base_url}{code}.csv"
    try:
        df = pd.read_csv(url)
        df["League"] = code  # добавляем колонку для идентификации лиги
        dataframes.append(df)
        print(f"✅ Загружено: {url}")
    except Exception as e:
        print(f"⚠️ Проблема с {url}: {e}")

# Объединяем все таблицы
combined = pd.concat(dataframes, ignore_index=True)
combined.to_csv("england_2425_combined.csv", index=False)
print("💾 Сохранено в файл england_2425_combined.csv")
