/*FIN3080-2021*Sample Code*/
**Q1 test CAPM**
* 一个stata的project的debug流程：在界面上写，边写边看dataset，然后把没报错的代码从command栏里面粘贴到do文件里面
* 还可以边写do file边跑，需要变量名就在右边点击界面然后复制粘贴
* 时刻记得ctrl+S保存

cd "D:\self_learning_Stata\project\FIN3080_project1_CAPM"

*数据处理


 **日度无风险利率，转成周度
import delimited "./raw_data/riskfree_daily.csv", clear
drop ïnrr1
gen month=substr(clsdt,1,7) //取一个string前七位，比如2017-01-13就变成2017-01
duplicates drop month,force
drop clsdt
duplicates drop nrrwkdt,force
clear //上一行直接drop重复值，发现只剩一个了，所以riskfree在2017.1-2020.12没变

 **市场周回报率
 **CSMAR下载的市场周回报率，每周有好几个市场的回报率，A股的B股的港股的等等，查看字段说明，我们就取type为5代表A股市场
import delimited "./raw_data/market_return_weekly.csv", clear
keep if ïmarkettype == 5 //CSMAR直接给了市场分类，5为全体A股
drop ïmarkettype
gen rf=0.01 * 0.0286 //注意原数据单位为%
save "./processed_data/mkt_return.dta",replace
clear

**股票周回报率
import delimited "./raw_data/stock_return_weekly.csv"
rename ïstkcd stkcd
format stkcd %06.0f  //转为6位数字
keep if markettype==1| markettype==4 //只要沪深主板+中小板
drop markettype
merge n:1 trdwnt using "./processed_data/mkt_return.dta" //merge函数，把现在界面打开的数据集和上面存的dta文件依据时间这一列合并到一个dataframe
//同时新增一列"_merge"，代表是否根据日期匹配成功
drop _merge //丢掉这一列
save "./processed_data/all_data_for_regression.dta",replace
* 把回归要用到的所有数据存储起来，后面使用

* CSMAR数据不能用现金红利再投资的，市场回报率需要用加权的，不能等权否则会受outlier影响
**将样本时间段分为三段
* 我们先在目前数据集基础上处理，分三段日期变量
* 真是感概，stata这些函数真是太强大的，只要会用可以简洁高效的完成各种分组
duplicates drop trdwnt ,force 
gen period=group(3) //卧槽，group函数直接生成一列标签为1-3，均分为三组
keep trdwnt period //丢掉某列就用drop，只保留某列就用keep
save "./processed_data/period_division.dta",replace 
clear

* 再次使用merge函数把分组情况添加到之前存储的数据集
use "./processed_data/all_data_for_regression.dta",clear
merge m:1 trdwnt using "./processed_data/period_division.dta"
drop _merge
save "./processed_data/all_data_for_regression.dta",replace

* 根据分组编号1,2,3把数据分别放到3个dta文件里面
use "./processed_data/all_data_for_regression.dta",clear
keep if period==1
save "./processed_data/group1.dta",replace

use "./processed_data/all_data_for_regression.dta",clear
keep if period==2
save "./processed_data/group2.dta",replace

use "./processed_data/all_data_for_regression.dta",clear
keep if period==3
save "./processed_data/group3.dta",replace

*第一组股票时间序列，回归得到个股beta
use "./processed_data/group1.dta",clear
gen ri_rf=wretnd-rf //因子模型左边，个股收益减去无风险
gen rm_rf=cwretmdos-rf //因子模型右边，只有市场因子需要减去无风险
sort stkcd trdwnt //依据优先级顺序对dataframe进行sort

by stkcd:reg ri_rf rm_rf //太牛逼了，直接用by函数，根据code分类做时间序列回归，reg Y X1 x2 x3
* stata做回归会自动忽略有缺失的地方
* 如果想剔除这段sample period出现过停牌的股票，不用他们的beta，就再加一步drop if number_of_obervations < 69，每个period是69周

* 没下载的函数，就 ssc install bcoeff
bcoeff ri_rf rm_rf , by(stkcd) g(b) se(se) //g代表generate
//这个时候查看数据，大量b的值缺失，因为缺失数据无法回归
duplicates drop stkcd,force //每个stock都对应beta，重复的很多
keep stkcd b //只要code和beta两列
sort b //根据beta从小到大
drop if b==. //删除回归的缺失值再分组
gen group=group(10) //分成十个portfolio
save "./processed_data/individual_betas.dta",replace


use "./processed_data/group2.dta",clear
merge m:1 stkcd using "./processed_data/individual_betas.dta"
//会有大量的没有match的，_merge这一列只有match成功的值是3，因此：
keep if _merge==3
drop _merge
bys group trdwnt: egen rr=mean(wretnd) //因为是根据两个变量分组计算，所以是bys不是by
duplicates drop group trdwnt,force
gen rp_rf=rr-rf
gen rm_rf=cwretmdos-rf
by group:reg rp_rf rm_rf
bcoeff rp_rf rm_rf , by(group) g(b_portfolio)
duplicates drop group,force
keep group b_portfolio
save "./processed_data/portfolio_betas.dta",replace

use "./processed_data/group3.dta",clear
merge m:1 stkcd using "./processed_data/individual_betas.dta"
keep if _merge==3
drop _merge 
gen ri_rf=wretnd-rf
bys group trdwnt: egen rp=mean(ri_rf)

merge m:1 group  using "./processed_data/portfolio_betas.dta"
drop _merge
gen rp_rf=rp-rf
gen rm_rf=cwretmdos-rf
duplicates drop group trdwnt,force
reg rp_rf b_portfolio

outreg2 using "./results/table.doc", replace tstat dec(2)


*note: q2 is portfolio sorting, please refer to tutorial-portfolio sorting.
