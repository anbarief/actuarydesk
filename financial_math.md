### financial_math

## Usage example:

The code below creates an `InterestRate` object that represents a 3% interest rate compounded annually, applicable from `t=0`. 
It also creates an object of `Contribution` that represents an investment deposit of 300 at time `t=3`. The `contribution.accumulate(10, [int_rate])` calculates the accumulated value of that investment at `t=10` (which means 7 years of growth), using scenario with interest rates `[int_rate]`.

```
import actuarydesk.financial_math as fm

int_rate = fm.InterestRate(0, 0.03, "annual")
contribution = fm.Contribution(3, 300)
contribution.accumulate(10, [int_rate])
```

---

The code below accumulates an investment of 300 made at time `t=3` up to time `t=10` with scenario of variable interest rate.
From time interval `[0, 4)` the applicable interest rate is 3% compounded annually, from time `[4, 5)` the applicable interest rate is 
2.5% compounded annually, from time `t=5` until forever, the applicable rate is a 1% discount rate compounded quarterly.

*If there are two or more interest rates with same time point, then the one with smallest index in the list will be used.

```
import actuarydesk.financial_math as fm

int1 = fm.InterestRate(0, 0.03, "annual")
int2 = fm.InterestRate(4, 0.025, "annual")
int3 = fm.InterestRate(5, 0.01, "quarter", discount=True)

contribution = fm.Contribution(3, 300)
contribution.accumulate(10, [int1, int2, int3])
```





