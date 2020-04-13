import pandas as pd
import plotly.express as px

df = pd.read_csv('pressure_0_3_seg.csv')
df = pd.read_csv('pressure.csv')
fig = px.line(df, x='iteration', y='tank_level', title='Tank level of minitown minicps')
fig.show()

df = pd.read_csv('pressure_empty_simulation.csv')
fig = px.line(df, x='iteration', y='tank_level', title='Tank level of minitown empty simulation minicps')
fig.show()

fig.show()
