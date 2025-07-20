import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# 读取数据文件
try:
    df = pd.read_csv('sydney_properties_working_final.csv')
except FileNotFoundError:
    print("Error: sydney_properties_working_final.csv not found in current directory")
    exit(1)
df = df[df['price_numeric'].notnull()].copy()
# print(df['price_numeric'].head(40))
# print(df['price_numeric'].isnull().sum())
