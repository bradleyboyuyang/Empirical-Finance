/*FIN3080-2021*Sample Code*/
**Q1 value factor**

clear all
set more off
cd "D:\self_learning_Stata\project\FIN3080_Project2_Value_Factor"

import delimited "FS_Combas.csv", encoding(UTF-8) 


// book value
generate date=date( accper , "YMD")
format date %td
gen month=month(date)
keep if month ==12
keep if typrep=="A"
rename a001222000 递延所得税资产
rename a002208000 递延所得税负债
rename a003112101 优先股账面值
rename a003000000 所有者权益合计


replace 递延所得税资产=0 if 递延所得税资产==.
replace 递延所得税负债=0 if 递延所得税负债==.
replace 优先股账面值=0 if 优先股账面值==.
replace 所有者权益合计=0 if 所有者权益合计==.
gen BE= 所有者权益合计+ 递延所得税负债- 递延所得税资产- 优先股账面值
save FS.dta

//clean monthly return 
import delimited "TRD_Mnth.csv", encoding(UTF-8) clear
gen month=substr( trdmnt,6,8)
destring month, replace
gen year=substr( trdmnt,1,4)
destring year, replace
save allmonth.dta

keep if month==12
save month_12.dta

//label SB for stock-year
use allmonth.dta
keep if month==6
save market_SB.dta


//generate median of the mainboard market
use market_SB.dta
keep if (markettype ==1)|(markettype ==4) // keep mainboard stocks only
bys year : egen year_med=median(msmvosd)
duplicates drop year, force //one year only one median
save mainboard_SB.dta


use market_SB.dta
keep if (markettype ==1)|(markettype ==4)|(markettype ==16) //Keep only A share and second board
merge m:1 year using mainboard_SB.dta
keep if _merge==3
drop _merge
gen SB=1 if msmvosd<year_med
replace SB=2 if msmvosd>=year_med //generate S and B label
label variable SB "=1 if Small, =2 if Big"
rename year yearSB
save SB.dta, replace


//To label HML for stock-year//
use FS.dta
gen year=substr( accper ,1,4)
destring year, replace
merge 1:1 year stkcd using month_12.dta
keep if _merge==3
drop _merge
gen B_M=BE/(msmvosd*1000) //get the B/M ratio (msmvosd unit: thound)
drop 递延所得税资产- 所有者权益合计 // drop the 4 aact variables
drop if B_M<=0
sort year B_M
save market_HML.dta


///this is for generate 30th and 70th quantile of the mainboard market
keep if (markettype ==1)|(markettype ==4)
bys year: egen year_BM_30 = pctile(B_M), p(30)
bys year: egen year_BM_70 = pctile(B_M), p(70)
duplicates drop year, force
save mainborad_HML.dta //this is the help dta file containing HML for merge


use market_HML.dta
keep if (markettype ==1)|(markettype ==4)|(markettype ==16) //Keep only A share and second board
merge m:1 year using mainborad_HML.dta
keep if _merge==3
drop _merge
gen HML=1 if B_M<year_BM_30 //1 is for L
replace HML=2 if (year_BM_30<=B_M)&(B_M<year_BM_70)
replace HML=3 if B_M>=year_BM_70 //generate H\M\L label
rename year yearHML
keep stkcd trdmnt yearHML markettype month HML
save HML.dta



// for the main file
use allmonth.dta
gen yearSB=year-1 if month==1|month==2|month==3|month==4|month==5|month==6
replace yearSB=year if yearSB==. //generate yearSB for merge with SB label 
gen yearHML=year-2 if month==1|month==2|month==3|month==4|month==5|month==6
replace yearHML = year-1 if yearHML==. //generate yearHML for merge with HML label 
merge m:1 stkcd yearSB using SB.dta
keep if _merge==3
drop _merge
merge m:1 stkcd yearHML using HML.dta
keep if _merge==3
drop _merge
save main.dta //stock-month


use main.dta
gen 账面市值比因子="SH" if HML==3&SB==1 //the third one--3
replace 账面市值比因子 = "BH" if HML==3&SB==2 //the first one--1
replace 账面市值比因子="SL" if HML==1&SB==1 //the forth one--4
replace 账面市值比因子="BL" if HML==1&SB==2 //the second one--2

//variable factor is generated for easy sorting as numerical//
sort trdmnt 账面市值比因子
gen factor=1 if 账面市值比因子=="BH"
replace factor=2 if 账面市值比因子=="BL"
replace factor=3 if 账面市值比因子=="SH"
replace factor=4 if 账面市值比因子=="SL"


//there should be one weighted average return for each month
bysort trdmnt 账面市值比因子:egen weight=pc( msmvosd ), prop
bysort trdmnt 账面市值比因子:egen ret_weight=sum( mretnd *weight)
duplicates drop trdmnt 账面市值比因子, force
drop if 账面市值比因子==""
sort trdmnt 账面市值比因子
bysort trdmnt 账面市值比因子:gen count=_n
bysort trdmnt 账面市值比因子:egen test=max(count)
sort trdmnt factor
bysort trdmnt: gen BL=ret_weight[_n+1]
bysort trdmnt: gen SH=ret_weight[_n+2]
bysort trdmnt: gen SL=ret_weight[_n+3]
rename ret_weight BH
gen BMfactor=(SH+BH)/2-(SL+BL)/2 
drop if BMfactor==.
save first.dta
use first.dta
gen marketType=1
save first_test.dta


//comparison
import delimited "STK_MKT_THRFACMONTH.csv", encoding(UTF-8) clear 
rename tradingmonth trdmnt
gen year=substr( trdmnt,1,4)
destring year, replace
drop if year<2006
gen marketType=1 if markettypeid=="P9709" //Keep only A share and second board
save FF.dta

use FF.dta, clear
duplicates drop marketType trdmnt, force
merge 1:1 marketType trdmnt using first_test.dta
keep if _merge==3 
drop _merge     
corr hml1 BMfactor
save final.dta


//plotting
generate date=date( trdmnt, "YM")
format month %tm
gen mon = mofd(date)
format mon %tm
rename hml1 CSMAR_factor
rename BMfactor Our_factor
tsset Our_factor mon
label variable CSMAR_factor "CSMAR factor values"
label variable Our_factor "self-constructed factor values"
tsline CSMAR_factor Our_factor



