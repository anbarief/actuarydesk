### actuarial_math

## Usage example:

The code below creates a term-life insurance model for an insured age `x=30` at issue with 30-year term, with benefit of 1000 payable at end year of insured's death. We calculate the APV by `termlife.calculate_apv()`. We can also calculate the level premium such that the expected loss is zero, by `termlife.minimum_level_premium()`.

```
import actuarydesk.financial_math as fm
import actuarydesk.actuarial_tables as at
import actuarydesk.actuarial_math as am

int_rate = fm.InterestRate(0, 0.04, 'annual')
table = at.table_dictionary['UK_ONS_2016_to_2018_male']

x = 30; term = 30
benefits = [am.Benefit(i, 1000) for i in range(x+1, x+term+1)]

termlife = am.TermLifeInsurance(x, term, benefits, [int_rate], table)

apv = termlife.calculate_apv()
minimum_premium = termlife.minimum_level_premium()
```
