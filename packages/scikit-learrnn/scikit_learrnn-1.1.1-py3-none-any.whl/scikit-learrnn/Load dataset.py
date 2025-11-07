import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

df= pd.read_csv('Data1.csv')
print(df,"\n")
imputer = SimpleImputer(missing_values = np.nan, strategy = 'most_frequent')
print(df.isnull().sum(),"\n")
df1 = imputer.fit_transform(df)
print(df1,"\n")
imputer1 = SimpleImputer(missing_values = np.nan, strategy='mean')
df[['Age','Income']]=imputer1.fit_transform(df[['Age','Income']])
print(df,"\n")
df[['Age','Income']] = df[['Age','Income']].fillna(df[['Age','Income']].mean())
