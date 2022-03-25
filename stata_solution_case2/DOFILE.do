//***********FIN3080-2021***********//
//**Porfotlio Sorting**SAMPLE CODE**//


/*Data Cleaning*/

*Import the csv data and save it as stata format
clear
import delimited C:\Users\jasmine\Desktop\raw.csv, encoding(utf8)
cd "C:\Users\tut3"
format stkcd %06.0f  //change the format of stock code
keep if markettype==1 | markettype==4 | markettype==16  //only A shares
sort stkcd trdmnt  //sort by stock and month
rename mretnd ret_current   //mark the current month return 
save "static.dta",replace
*Save a return data for merge 
rename trdmnt month
rename ret_current ret
keep stkcd month ret
save "return.dta",replace

/*Merge last month return*/
use "static.dta",clear
rename lastmonth month
merge 1:1 stkcd month using "return.dta"
drop if _merge==2
rename ret ret_lastm
drop _merge

drop if trdmnt=="2017/11"
drop if trdmnt=="2017/12"

  /*
  /*check whether there are missing values*/
  
  preserve 
  duplicates drop stkcd,force
  sum stkcd
  restore
  
  bys trdmnt: sum stkcd //for each month,check the number of stocks

  sort stkcd trdmnt
  bys stkcd: egen count=count(trdmnt)
 
  sort count stkcd trdmnt
  */
 

/*Sorting*/

*Drop missing values
drop if ret_current==.
drop if ret_lastm==.

*Each month sort out 10 groups, by last month return
sort trdmnt ret_lastm
bys trdmnt: gen group=group(10)

*Calculate average return for each group (equal weighted)
bys group: egen average_ret=mean(ret_current)
replace average_ret=average_ret*100

save "final.dta",replace
duplicates drop group,force
keep group average_ret
save "ret_group.dta",replace
