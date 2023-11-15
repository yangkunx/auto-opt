import pandas as pd

df = pd.DataFrame()
df = pd.DataFrame(columns=['Name', 'Age'])

df = pd.concat([df, pd.DataFrame([['John', 25]], columns=['Name', 'Age'])], ignore_index=True)
df = pd.concat([df, pd.DataFrame([['Mary', 30]], columns=['Name', 'Age'])], ignore_index=True)
df = pd.concat([df, pd.DataFrame([['Peter', 28]], columns=['Name', 'Age'])], ignore_index=True)

df['Salary'] = pd.Series([50000, 60000, 70000], index=df.index)
df['City'] = ['New York', 'Los Angeles', 'Chicago']

print(df)