import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tushare as ts
import scipy

plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

# code_list = ['000001','600000','600030','600519','000672','601857','002230','000538']
code_list = ['600519', '000651', '000002', '601318', '601857']
start_date = '20150101'
end_date = '20191231'
risk_free_daily = 0.000041 #假定的日度化无风险利率

# efficient frontier用return或者log_return画都是成立的
def get_data(code: np.str, start_date:np.str, end_date:np.str) -> pd.DataFrame:
    ts.set_token('0d86b9a1aa5a9ba78b7e3a2feba63242abaeae62c777f5742f6cf698')
    pro = ts.pro_api() 
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    code = data[data['symbol']==code]['ts_code'].values.tolist()[0] #tushare的pro_bar参数里code需要有后缀

    df = ts.pro_bar(api=pro, ts_code=code, adj='qfq', start_date=start_date, end_date=end_date) 
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d') 
    df = df.set_index('trade_date', drop=False) 
    df.index.name = 'Date'
    df = df.sort_index()
    df['return'] = df['close']/df['pre_close'] - 1 #用这一行或下一行对数收益率画efficient frontier都是生效的
    df['log_return'] = np.log(df['close']/df['pre_close'])
    #df['log_return'] = df['log_return'].shift(-2) #这步平移不是必须的
    df.dropna(inplace=True)
    return df

def ret_weight(df:pd.DataFrame, weight:np.array): 
    mean = df.mean()*252
    return sum(weight * mean)

def std_weight(df:pd.DataFrame, weight:np.array): 
    cov = df.cov()*252
    var = np.dot(weight, cov)
    var = np.dot(var, weight.T)
    std = np.sqrt(var)
    return std

def construct_portfolio(code_list, start_date, end_date) -> pd.DataFrame:
    nums = []
    for code in code_list:
        df = get_data(code, start_date, end_date)
        ret = df[['return']]
        ret = ret.rename(columns={'return':'return_%s'%code})
        nums.append(ret)
    ret_combined = pd.concat(nums, axis=1, join='inner')
    return ret_combined

def construct_portfolio_with_riskfree(code_list, start_date, end_date) -> pd.DataFrame:
    ret_combined = construct_portfolio(code_list, start_date, end_date)
    ret_combined['riskfree'] = risk_free_daily # 添加日度化无风险利率，因为获取的收益率也是日度的
    return ret_combined

def feasible_region_drawing(df:pd.DataFrame, N):
    stds = []
    rets = []
    sharpe_ratio = []
    for _ in range(10000):
        weight = np.random.rand(N)
        weight /= sum(weight)
        ret = ret_weight(df,weight)
        std = std_weight(df,weight)
        rets.append(ret)
        stds.append(std)
        sharpe = (ret-risk_free_daily*252)/std
        sharpe_ratio.append(sharpe)
    plt.scatter(stds, rets, c=sharpe_ratio,cmap='RdYlGn', edgecolors='black',marker='o') #不同的cmap，不同的炫酷效果
    #plt.scatter(stds, rets, c=sharpe_ratio,cmap='cool', alpha=0.4, edgecolors='blue', marker='o')
    #plt.scatter(stds, rets, color='#660066') 
    #plt.plot(stds, rets, color='#660066', linestyle='dashdot') #把点用线连起来，连成一整个区域

def calculate_opt_weight(given_ret, df:pd.DataFrame, N):
    x0 = np.repeat(1/N, N)
    bounds = tuple((0,1) for _ in range(N))
    constraints = [{'type':'eq','fun':lambda x: sum(x)-1}, {'type':'eq','fun': lambda x: ret_weight(df,x)-given_ret}]
    outcome = scipy.optimize.minimize(lambda x: std_weight(df,x),x0=x0, constraints=constraints,bounds=bounds)
    return outcome.fun,outcome.x

def calculate_sharpe(given_return, df:pd.DataFrame, N):
    opt_std, opt_weight = calculate_opt_weight(given_return, df, N)
    opt_ret = ret_weight(df, opt_weight)
    intercept = risk_free_daily*252
    return (opt_ret-intercept)/opt_std
    

def efficient_frontier_drawing(df:pd.DataFrame, N):
    #关于given_return的设置，如果单单想画抛物线或者可行域就可以range设的广一些，但如果为了看上半部分和直线的切线就不要
    #范围取太广，这个given_return可以自己手动设置，也可以取一个np.min,np.max的一个大致估计值。
    #given_ret = np.arange(-0.025, 0.4, .001)
    given_ret = np.linspace(0.3, 0.43, num=500)
    calculated_std = []
    for i in given_ret:
        calculated_std.append(calculate_opt_weight(i, df, N)[0])
    sharpe_ratio = (given_ret-risk_free_daily*252)/np.array(calculated_std)
    #plt.scatter(calculated_std, given_ret, color='#660066',alpha=0.7, linewidths=0.5, edgecolors='#680808')
    plt.scatter(calculated_std, given_ret, c=sharpe_ratio, cmap='RdYlGn', alpha=0.7, edgecolors='black',marker='o')
    #plt.plot(calculated_std, given_ret, color='#680808',alpha=0.7, linewidth=2.5, linestyle='dashdot')

if __name__ == '__main__':
    plt.style.use('seaborn-dark')
    plt.figure(figsize=(9, 5))
    portfolio = construct_portfolio(code_list, start_date, end_date)
    portfolio_with_riskfree = construct_portfolio_with_riskfree(code_list,start_date,end_date)
    #画可行域：
    #feasible_region_drawing(portfolio,len(portfolio.columns))
    #feasible_region_drawing(portfolio_with_riskfree,len(portfolio_with_riskfree.columns))
    #求解最佳权重：
    #calculate_opt_weight(0.16,portfolio,len(portfolio.columns))
    #calculate_opt_weight(0.16,portfolio_with_riskfree,len(portfolio_with_riskfree.columns))
    #画有效边界：
    #efficient_frontier_drawing(portfolio,len(portfolio.columns))
    #efficient_frontier_drawing(portfolio_with_riskfree,len(portfolio_with_riskfree.columns))

    #算夏普：
    #print('Sharpe Ratio: ', calculate_sharpe(0.3, portfolio_with_riskfree, len(portfolio_with_riskfree.columns)))

    #画一个不带无风险和带无风险的在一个图上，抛物线切线
    # efficient_frontier_drawing(portfolio,len(portfolio.columns))
    # efficient_frontier_drawing(portfolio_with_riskfree,len(portfolio_with_riskfree.columns))

    feasible_region_drawing(portfolio,len(portfolio.columns))
    efficient_frontier_drawing(portfolio_with_riskfree,len(portfolio_with_riskfree.columns))
    plt.grid(True)
    plt.xlabel('expected volatility')
    plt.ylabel('expected return')
    plt.colorbar(label='Sharpe ratio')
    plt.savefig('Efficient_frontier.png',dpi=1000)
    plt.show()


# 进一步完善方向：
# 曲线equation怎么算
# 美化图片
