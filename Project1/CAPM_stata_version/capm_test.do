/*FIN3080-2021*Sample Code*/
**Q1 test CAPM**

cd "C:\Users\Fin3080 project1"

*data cleaning
 **risk free rate
import delimited "C:\Users\Fin3080 project1\TRD_Nrrate.csv", clear
drop ïnrr1
gen month=substr(clsdt,1,7)
duplicates drop month,force
drop clsdt
duplicates drop nrrwkdt,force
clear //rf did not change in this period

 **market return
import delimited "C:\Users\Fin3080 project1\TRD_Weekcm.csv", clear
keep if ïmarkettype ==5
drop ïmarkettype
gen rf=0.0286
save "mkt ret.dta",replace


import delimited "C:\Users\Fin3080 project1\TRD_Week.csv"
rename ïstkcd stkcd
format stkcd %06.0f  //6 digits stock code
keep if markettype==1| markettype==4 //shanghai shenzhen mainboard
drop markettype
merge n:1 trdwnt using "mkt ret.dta"
drop _merge
save "static.dta",replace



*divide the sample period into 3 

 /*create period var*/
duplicates drop trdwnt ,force 
gen period=group(3)
keep trdwnt period
save "period.dta",replace 

 /*merge back the period var*/
use "static.dta",clear
merge m:1 trdwnt using "period.dta"
drop _merge
 /*merge back the period var*/

save "static.dta",replace

 /*create three subsample*/

use "static.dta",clear
keep if period==1
save "sta1.dta",replace

use "static.dta",clear
keep if period==2
save "sta2.dta",replace

use "static.dta",clear
keep if period==3
save "sta3.dta",replace


*use sample 1 for betas
use "sta1.dta",clear
gen ri_rf=wretnd-rf
gen rm_rf=cwretmdos-rf
sort stkcd
by stkcd:reg ri_rf rm_rf
bcoeff ri_rf rm_rf , by(stkcd) g(b) se(se) //each stock has a beta
duplicates drop stkcd,force
keep stkcd b 
sort b
gen group=group(10)
save "betas.dta",replace


use "sta2.dta",clear
merge m:1 stkcd using "betas.dta"
keep if _merge==3
drop _merge
bys group trdwnt: egen rr=mean(wretnd)
duplicates drop group trdwnt,force
gen rp_rf=rr-rf
gen rm_rf=cwretmdos-rf
by group:reg rp_rf rm_rf
bcoeff rp_rf rm_rf , by(group) g(b_portfolio)
duplicates drop group,force
keep group b_portfolio
save "beta_p.dta",replace

use "sta3.dta",clear
merge m:1 stkcd using "betas.dta"
keep if _merge==3
drop _merge 
gen ri_rf=wretnd-rf
bys group trdwnt: egen rp=mean(ri_rf)

merge m:1 group  using "beta_p.dta"
drop _merge
gen rp_rf=rp-rf
gen rm_rf=cwretmdos-rf
duplicates drop group trdwnt,force
reg rp_rf b_portfolio

outreg2 using "table.doc", replace tstat dec(2)


*note: q2 is portfolio sorting, please refer to tutorial-portfolio sorting.
