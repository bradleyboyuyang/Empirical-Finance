# %%
import os
print(os.getcwd())
# %%
import pandas as pd
import numpy as np
# %%
ind_return = pd.read_csv('../week-individual-return/ERCR_Awklyr.csv')
ind_return['Stkcd'] = ind_return['Stkcd'].map(lambda d: '%06d'%d)
ind_return['Trddt'] = pd.to_datetime(ind_return['Trddt'])
ind_return.columns = ['code', 'date', 'return']
ind_return = ind_return[ind_return['code'].map(lambda s: s.startswith('60') \
                                                    or s.startswith('00') \
                                                    or s.startswith('900') \
                                                    or s.startswith('200'))]
# %%
# ind_return[~ind_return.isnull()]
# %%
null = ~ind_return.isnull().to_numpy()
# %%
notnull = null[:, 0] & null[:, 1] & null[:, 2]
ind_return.loc[~notnull]
# %%
missing = ind_return.loc[~notnull]
len(missing['code'].unique())
# %%
missing_date = missing.groupby(by='code').apply(lambda df: df['date'])
# %%
missing.describe()
# %%
# filter stocks listed after 2017-1-6
start_date = ind_return.groupby('code').apply(lambda df: df['date'].min())
start_date = pd.DataFrame({'code': start_date.index.to_numpy(),
                           'date': start_date.to_numpy()})
start_date
# %%
start_after = start_date['date'] > '2017-01-06'
start_after = start_date.loc[start_after]
# %%
start_after_code_list = start_after['code'].to_numpy().tolist()
start_after_code_list
# %%
len(ind_return['code'].unique())
# %%
availables = ind_return[~ind_return['code'].isin(start_after_code_list)]
availables
# %%
availables.describe()
# %%
len(availables['code'].unique())
# %%
avg_return = availables.groupby('code')['return'].mean()
avg_return = pd.DataFrame({'code': avg_return.index,
                           'avg': avg_return.to_numpy()})
availables = pd.merge(availables, avg_return, on='code', how='left')
availables
# %%
availables.loc[availables['return'].isnull(), 'return'] = availables[availables['return'].isnull()]['avg']
availables['return'].isnull().sum()
# %%
availables.info()
# %%
availables = availables.drop('avg', axis=1)
availables['return'].plot(kind='hist')
# %%
availables
# %%
availables.to_csv('./availables.csv', index=False)
# %%
%reset -f
import pandas as pd
import numpy as np
from datetime import datetime
# %%
gross = pd.read_csv('../week-gross-return/TRD_Weekcm.csv')
gross
# %%
gross.info()
# %%
gross['Trdwnt'].unique()
# %%
market = pd.DataFrame({'week': gross['Trdwnt'], 'return': gross['Cwretwdeq']})
market
# %%
market['date'] = market['week'].apply(lambda s: datetime.strptime(s + '-5', '%Y-%W-%w'))
market
# %%
market = market.drop_duplicates('date')
market
# %%
market.isnull().sum()
# %%
market.to_csv('./market.csv', index=False)
# %%
%reset -f
import pandas as pd
import numpy as np
from datetime import datetime
# %%
availables = pd.read_csv('./availables.csv')
market = pd.read_csv('./market.csv')
# %%
availables['date'] = pd.to_datetime(availables['date'])
availables['week'] = availables['date'].dt.week
availables['year'] = availables['date'].dt.year
availables
# %%
market
# %%
market['code'] = 'm'
market['year'] = market.apply(lambda df: df['week'].split('-')[0], axis=1)
market['week'] = market.apply(lambda df: df['week'].split('-')[1], axis=1)
market
# %%
market['week'] = market['week'].astype(int)
market
# %%
gross = pd.concat([availables, market])
gross['year_week'] = gross.apply(lambda df: '%d-%02d'%(int(df['year']), df['week']), axis=1)
gross
# %%
gross.to_csv('./gross.csv', index=False)
# %%
gross.info()
# %%
gross.isnull().sum()
# %%
gross = gross.drop_duplicates(['code', 'year_week'])
gross
# %%
pivot = pd.pivot(gross, 'year_week', 'code', 'return')
pivot
# %%
pivot = pivot.drop('2020-53')
pivot
# %%
pivot.isnull().sum()
# %%
pivot[1].loc[pivot[1].isnull()]
# %%
pivot.loc['2019-53']
# %%
pivot = pivot.drop('2019-53')
pivot.isnull().sum().value_counts()
# %%
pivot.isnull().sum()
# %%
pivot['m'][pivot['m'].isnull()]
# %%
pivot = pivot.drop('2020-01')
pivot.isnull().sum().value_counts()
# %%
pivot.index
# %%
pivot = pivot.sort_index()
pivot
# %%
period_1 = pivot.iloc[:67]
period_2 = pivot.iloc[67:134]
period_3 = pivot.iloc[134:]
# %%
period_1.to_csv('./p1.csv')
period_2.to_csv('./p2.csv')
period_3.to_csv('./p3.csv')
# %%
import matplotlib.pyplot as plt
def get_beta(s1, s2):
    df = pd.concat([s1, s2], axis=1)
    df = df.dropna(axis=0)
    df.columns = ['y', 'x']
    x = df['x'].to_numpy()
    y = df['y'].to_numpy()
    # plt.plot(x, y, '.')
    x_bar = np.average(x)
    y_bar = np.average(y)
    x = x - x_bar
    y = y - y_bar
    return np.matmul(x.T, y) / np.matmul(x.T, x)

get_beta(period_1[600029], period_1['m'])
# %%
m = period_1['m']
stocks = period_1.drop('m', axis=1)
betas = stocks.apply(lambda s: get_beta(s, m), axis=0)
betas
# %%
betas = pd.DataFrame({'code': betas.index,
                      'beta': betas.to_numpy()})
betas
# %%
betas = betas.sort_values('beta', ascending=False)
betas
# %%
n = 100
total = betas.shape[0]
group = np.zeros((total,))
size = int(total/n)
for i in range(n-1):
    group[i*size:(i+1)*size] = i
group[(n-1)*size:] = n-1
group
# %%
betas['group'] = group
betas
# %%
betas['group'] = betas['group'].astype(int)
betas = betas.sort_index()
betas
# %%
betas.to_csv('./group.csv', index=False)
# %%
# betas = betas.drop('beta', axis=1)
betas['code'] = betas['code'].astype(str)
# %%
period_2 = pd.read_csv('./p2.csv')
period_2
# %%
p2 = pd.melt(period_2, 'year_week', period_2.columns[1:], var_name='code', value_name='return')
p2
# %%
p2 = pd.merge(p2, betas, on='code', how='left')
p2
# %%
p2.loc[p2['code'] == 'm', 'group'] = -1
p2['group'] = p2['group'].astype(int)
p2
# %%
# pivot = pd.pivot(p2, 'year_week', ['group', 'code'], 'return')
# pivot
# %%
p2.groupby('code').apply(lambda df: df['return'].isnull().sum()).value_counts()
# %%
period_3 = pd.read_csv('./p3.csv')
period_3
# %%
((period_3.isnull().sum().value_counts()).index > 5).sum()
# %%
missing = period_3.isnull().sum()
missing = missing[missing == 0]
valid_stocks = missing.index.to_numpy().tolist()
len(valid_stocks)
# %%
valid_stocks.append('m')
p2 = p2[p2['code'].isin(valid_stocks)]
p2
# %%
groups = p2.groupby('group').apply(lambda df: df.groupby('year_week')['return'].mean())
groups
# %%
groups = groups.transpose()
groups
# %%
groups.columns = ['m'] + groups.columns[1:].to_numpy().tolist()
groups
# %%
groups.isnull().sum().value_counts()
# %%
m = groups['m']
portfolios = groups.drop('m', axis=1)
betas = portfolios.apply(lambda s: get_beta(s, m), axis=0)
betas
# %%
betas = pd.DataFrame({'id': betas.index,
                      'beta': betas.to_numpy()})
betas
# %%
betas.to_csv('./beta.csv', index=False)
# %%
group = pd.read_csv('./group.csv')
group
# %%
period_3
# %%
p3 = pd.melt(period_3, 'year_week', period_3.columns[1:], var_name='code', value_name='return')
p3
# %%
p3 = p3[p3['code'].isin(valid_stocks)]
p3
# %%
group['code'] = group['code'].astype(str)
p3 = pd.merge(p3, group, on='code', how='left')
p3
# %%
p3.loc[p3['code'] == 'm','group'] = -1
# p3 = p3.drop('beta', axis=1)
p3['group'] = p3['group'].astype(int)
p3
# %%
groups = p3.groupby('group').apply(lambda df: df.groupby('year_week')['return'].mean())
groups
# %%
groups = groups.transpose().mean()
# %%
groups
# %%
groups = pd.DataFrame({'id': groups.index,
                       'avg_return': groups.to_numpy()})
groups.isnull().sum()
# %%
groups.to_csv('./avg_returns.csv', index=False)
# %%
betas
# %%
groups = pd.read_csv('./avg_returns.csv')
groups = groups.iloc[1:]
# groups = group.drop(0, axis=0)
groups
# %%
total = pd.merge(betas, groups, on='id')
total
# %%
total.to_csv('./total.csv', index=False)
# %%
import pandas as pd
import numpy as np
import statsmodels.api as sm
# %%
p1 = pd.read_csv('./p1.csv')
p1
# %%
def linear_regress(s1, s2):
    df = pd.concat([s1, s2], axis=1)
    df = df.dropna(axis=0)
    df.columns = ['y', 'x']
    x = df['x'].to_numpy()
    y = df['y'].to_numpy()
    X = sm.add_constant(x)
    model = sm.OLS(y, X)
    rs = model.fit()
    return rs.params.tolist() + \
        rs.tvalues.tolist() + \
        rs.pvalues.tolist() + \
        [rs.rsquared, rs.rsquared_adj]

rs = linear_regress(p1['1'], p1['m'])
rs
# %%
m = p1['m']
stocks = p1.drop('m', axis=1)
stocks = stocks.drop('year_week', axis=1)
betas = stocks.apply(lambda s: linear_regress(s, m), axis=0)
betas
# %%
betas = pd.DataFrame({
    'code': betas.index,
    'content': betas.to_numpy()
})
betas
# %%
cols = ['a', 'b', 'a_t', 'b_t', 'a_p', 'b_p', 'r_sq', 'r_sq_adj']
content = np.array(betas['content'].to_numpy().tolist())
for i in range(8):
    betas[cols[i]] = content[:, i]
betas
# %%
betas = betas.drop('content', axis=1)
betas
# %%
betas.to_csv('./p1_regression.csv', index=False)
# %%
p2 = pd.read_csv('./p2.csv')
p2
# %%
p2 = pd.melt(p2, 'year_week', p2.columns[1:], var_name='code', value_name='return')
p2
# %%
group = pd.read_csv('./group.csv')
group
# %%
p3 = pd.read_csv('./p3.csv')
missing = p3.isnull().sum()
missing = missing[missing == 0]
valid_stocks = missing.index.to_numpy().tolist()
len(valid_stocks)
# %%
group['code'] = group['code'].astype(str)
p2 = pd.merge(p2, group, on='code', how='left')
p2
# %%
p2.loc[p2['code'] == 'm', 'group'] = -1
p2['group'] = p2['group'].astype(int)
p2
# %%
p2 = p2.drop('beta', axis=1)
p2
# %%
p2['return'] = p2['return'] - 0.000286
groups = p2.groupby('group').apply(lambda df: df.groupby('year_week')['return'].mean())
# groups
groups = groups.transpose()
groups
# %%
m = groups[-1]
portfolios = groups.drop(-1, axis=1)
# stocks = stocks.drop('year_week', axis=1)
betas = portfolios.apply(lambda s: linear_regress(s, m), axis=0)
display(betas)
betas = pd.DataFrame({
    'code': betas.index,
    'content': betas.to_numpy()
})
display(betas)
cols = ['a', 'b', 'a_t', 'b_t', 'a_p', 'b_p', 'r_sq', 'r_sq_adj']
content = np.array(betas['content'].to_numpy().tolist())
for i in range(8):
    betas[cols[i]] = content[:, i]
display(betas)
betas = betas.drop('content', axis=1)
betas
# %%
betas.to_csv('./p2_regression.csv', index=False)
# %%
betas = pd.read_csv('./p1_regression.csv')
betas
# %%
des = betas.describe()
des
# %%
des.to_csv('./p1_overall.csv')
# %%
des = pd.read_csv('./p2_overall.csv')
# display(des)
des.columns = ['type'] + des.columns.to_numpy().tolist()[1:]
# display(des)
# des.index = des['type']
# des = des.drop('type', axis=1)
# des.columns = ['type'] + des.columns.to_numpy().tolist()[1:]
des.index = des['type']
des = des.drop('type', axis=1)
des = des.drop('code', axis=1)
des = des.drop('r_sq_adj', axis=1)
# display(des)
des.columns = ['alpha', 'beta', 'alpha_t', 'beta_t', 'alpha_p', 'beta_p', 'R^2']
des
# %%
