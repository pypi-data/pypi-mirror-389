#B.	) Create or explore datasets to use all pre-processing routines like label encoding and scaling
#1. Implementing Scaler
import pandas as pd
From sklearn.datasets import load_iris
From sklearn.preprocessing import StandardScaler, MinMaxScaler
iris=load_iris()
df=pd.DataFrame(iris.data,columns=iris.feature_names)
print("Original iris Data(first 5 rows)")
print(df.head(),"\n")
Standard_scaler = StandardScaler()
iris_Standard =  Standard_scaler.fit_transform(df)
print("StandardScaler(mean=0,Std=1)")
print(pd.DataFrame(iris_Standard,columns=df.columns).head(),"\n")
minmax_scaler = MinMaxScaler()
iris_minmax = minmax_scaler.fit_transform(df)
print("MinMaxScaler(min=0,max=1)")
print(pd.DataFrame(iris_minmax,columns=df.columns).head(),"\n")

#2. Data Preprocessing using Encoder
CODE:
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = [iris.target_names[i] for i in iris.target]
print(" Original data (first 5 rows)")
print(df.head(),"\n")

label_encoder = LabelEncoder()
df['species_label']= label_encoder.fit_transform(df['species'])
print("classes found (LabelEncoder):", label_encoder.classes_)
print("\nData after Label Encoder (first 5 rows):")
print(df[['species','species_label']].head(),"\n")

one_hot_encoder = OneHotEncoder(sparse_output = False)
species_reshaped= df['species'].values.reshape(-1,1)
species_one_hot= one_hot_encoder.fit_transform(species_reshaped)
one_hot_df = pd.DataFrame(species_one_hot, columns=one_hot_encoder.get_feature_names_out(['species']))
df = pd.concat([df, one_hot_df], axis=1)
print("One-Hot Encoded column names:", one_hot_df.columns.tolist())
print("One-Hot Encoder (first 5 rows):")
print(df.head())


#C.) Load a dataset, calculate descriptive summary statistics, create visualisations using different graphs, and identify potential features and target variables.

CODE:
from sklearn.datasets import load_iris
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
data = load_iris()
print(data.feature_names,"\n")
df = pd.DataFrame(data.data, columns=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'])
df['target'] = data.target
print(df.head(2),"\n")

print(df.info(),"\n")
print(df.describe(),"\n")
num_cols=['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
for col in num_cols:
    plt .figure(figsize=(6,4))
    sns.histplot(df[col],color='skyblue')
    plt.xlabel(col)
    plt.ylabel('frequency')

sns.countplot(x='target',data=df)
plt.title("count of species")
plt.xlabel('species')
plt.ylabel('Frequency')
for col in num_cols:
    plt.figure(figsize=(6,4))
    sns.boxplot(y=df[col],color='Lightgreen')
sns.scatterplot(x='sepal_length',y='petal_length',data=df,hue='target')
plt.xlabel('Sepal_length')
plt.ylabel('Petal_length')

sns.boxplot(x='target',y='sepal_length',data=df,color='lightgreen')
corr = df.iloc[:, :-1].corr()
print(corr, "\n")
sns.heatmap(corr,annot=True)
sns.pairplot(df,hue='target')
