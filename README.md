# actuarydesk

These modules are aimed to become a tool for actuary to model and analyze simple products or for actuarial students to practice. 

Date: 29-8-2020

Author: Arief Anbiya - anbarief (at) live (dot) com

Version: 0.1.4

Requirements: Python >= 3.6, Pandas

website: https://pypi.org/project/actuarydesk/

---

Documentation: ....

Dataset download for `math_economics_viz`: [dataset link](https://drive.google.com/drive/folders/1n8XRWpmX1tOz1Uu1PaT9gXv9Feu4-k5i?usp=sharing)

---

Installation: `py -m pip install actuarydesk`

---

Example of using the `financial_math.py`: analysing the growth of money from investments made at time 0, 1, and 1.5 with amount of 100, 100, and 200 respectively.
Assuming the interest rate is 0.04 annually for the first year and 0.03 semi-annually after that.

```

import actuarydesk.financial_math as fm

deposits = [fm.Contribution(0, 100), \
            fm.Contribution(1, 100), \
            fm.Contribution(1.5, 200)]
int_rates = [fm.InterestRate(0, 0.04, 'annual'), \
             fm.InterestRate(1, 0.03, 'semi-annual')]
timeline = fm.FinancialTL(deposits, int_rates)

print(timeline.acc_value_at_point(5))
dynamics = timeline.acc_value_dynamics(5, 0.5)
dynamics_df = timeline.acc_value_dynamics_df(5, 0.5)
present_value = timeline.value_at(0)

```

Example of generating a cashflow for a particular policy modeled by a particular actuarial model: insured age 50 with a 15-year life insurance term, the benefit amount is 10000 
payable at the end year of death, the level-premium are paid at beginning of each year until term ends or as long as survival.

```

import actuarydesk.financial_math as fm
import actuarydesk.actuarial_tables as at
import actuarydesk.actuarial_math as am

table = at.UK_ONS_2016_to_2018_male
int_rate = [fm.InterestRate(0, 0.05, 'annual')]
x = 50; term = 15;
benefits = [am.Benefit(i, 10000) for i in range(x+1, x+term+1)]
ins_model = am.TermLifeInsurance(x, term, benefits, int_rate, table)
model = am.ActuarialModel(ins_model, ['due', 'annual'], 2020)
reserves = model.reserves_dynamics_df(0.5, 70)
cashflow = model.cashflow_df(65)

```
---

The tables are collected from: https://www.ons.gov.uk/ , https://mort.soa.org/
