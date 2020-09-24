import math
import random

import pandas

import actuarydesk.actuarial_tables as at
import actuarydesk.financial_math as fm

def t_p_x(x, t, table):
    lower_t = math.floor(t); dt = t - lower_t
    upper_x = math.ceil(x); dx = upper_x - x
    px = table['px']; qx = table['qx']; prob = 1
    if (x+t) > len(px):
        return 0
    elif t == 0:
        return 1
    else:
        if (dt==0) and (dx==0):
            x=int(x); t=int(t);
            for i in px[x:x+t]:
                prob = prob*i
            return prob
        elif (dt==0) and (dx!=0):
            t=int(t)
            return t_p_x(upper_x, t, table)*(1-dx*table['qx'][math.floor(x)])
        elif (dt!=0) and (dx==0):
            x=int(x)
            if x+t < x+1:
                return 1-t*table['qx'][x]
            if x+t > x+1:
                return t_p_x(x, math.floor(x+t)-x, table)*t_p_x(math.floor(x+t), x+t-math.floor(x+t), table)
        else:
            if x+t < upper_x:
                return 1-t*table['qx'][math.floor(x)]
            elif x+t > upper_x:
                return (1-dx*table['qx'][math.floor(x)])*(t_p_x(upper_x, x+t-upper_x, table))
            else:
                return 1-t*table['qx'][math.floor(x)]
            
def t_q_x(x, t, table):
    return 1-t_p_x(x,t,table)

def find_premium(x, t, benefits, interest_rates, table, premium_time_points, loss_bound = 0.5, loss_target = 0, start_premium = 0, dp = 0.25, max_iter = 10000):
    insurance = TermLifeInsurance(x, t, benefits, interest_rates, table)
    if start_premium == 0:
        premium = dp
    else:
        premium = start_premium
    annuity = TermLifeAnnuity(x, t, [Premium(i, premium) for i in premium_time_points], interest_rates, table)
    loss = insurance.calculate_apv() - annuity.calculate_apv()
    iter_num = 0
    while abs(loss-loss_target) > abs(loss_bound):
        if iter_num == max_iter:
            return None
        premium = premium + dp
        annuity.payments = [Premium(i, premium) for i in premium_time_points]
        annuity.adjustments()
        loss = insurance.calculate_apv()-annuity.calculate_apv()
        iter_num += 1
    print("Expected Loss = {}".format(loss))
    return premium

def combined_two_cashflows(cashflow_df1, cashflow_df2, interest_rates, collective_interest_rates=None):
    if collective_interest_rates == None:
        collective_interest_rates = [fm.InterestRate(0, 0, 'annual')]
    cols = ['profit_exclude_collective_fund', 'income', 'expense', 'income_from_collective_fund']
    t_pols = sorted(list(set(list(cashflow_df1.t_policy) + list(cashflow_df2.t_policy))))
    df = pandas.DataFrame(t_pols, columns=['t_policy'])
    for col in cols:
        results = []
        for t in t_pols:
            result1 = cashflow_df1[cashflow_df1.t_policy==t][col]
            result2 = cashflow_df2[cashflow_df2.t_policy==t][col]
            if len(result1)==0:
                result1 = 0
            else:
                result1 = result1.values[0]
            if len(result2)==0:
                result2 = 0
            else:
                result2 = result2.values[0]
            results.append(result1+result2)
            prev_results = (result1, result2)
        df[col] = pandas.Series(results)
    exp_contributions = [fm.Contribution(df.t_policy[i], df.profit_exclude_collective_fund[i]) for i in range(len(df))]
    exp_contributions_fund = [fm.Contribution(df.t_policy[i], df.income_from_collective_fund[i]) for i in range(len(df))]
    accumulated = []
    for i in range(1, len(exp_contributions)+1):
        involved = exp_contributions[0:i]
        total = sum([j.accumulate(involved[-1].t, interest_rates)  for j in involved])
        accumulated.append(total)
    accumulated_2 = []
    for i in range(1, len(exp_contributions_fund)+1):
        involved = exp_contributions_fund[0:i]
        total = sum([j.accumulate(involved[-1].t, collective_interest_rates)  for j in involved])
        accumulated_2.append(total)
    df['accumulated_profit_exclude_collective_fund'] = pandas.Series(accumulated, index = df.index)
    df['accumulated_income_collective_fund'] = pandas.Series(accumulated_2, index = df.index)
    df['total_accumulated_profit'] = df['accumulated_profit_exclude_collective_fund'] + df['accumulated_income_collective_fund']
    return df

def combined_cashflows(cashflows, interest_rates, collective_interest_rates = None):
    df1 = cashflows[0]; df2 = cashflows[1]
    df = combined_two_cashflows(df1, df2, interest_rates, collective_interest_rates)
    for cf in cashflows[2:]:
        df = combined_two_cashflows(df, cf, interest_rates, collective_interest_rates)
    return df


class Benefit(fm.Contribution):

    def __init__(self, t, amount, endowment = False):
        super().__init__(t, amount)
        self.t = math.ceil(t)
        self.endowment = endowment

    def claim_prob(self, x, table):
        if self.endowment:
            return t_p_x(x, max(self.t-x, 0), table) 
        return t_p_x(x, max(self.t-x-1, 0), table)*t_q_x(x + max(self.t-x-1, 0), self.t - x - max(self.t-x-1, 0), table)

    def expected_at(self, x, table, interest_rates):
        if self.t > x:
            return self.claim_prob(x, table)*self.value_at(x, interest_rates)
        else:
            return 0


class Premium(fm.Contribution):

    def __init__(self, t, amount, collective_fund_proportion = 0):
        super().__init__(t, amount)
        self.t = t
        self.original_amount = amount
        self._collective_fund_premium = None
        self.original()
        if (0<collective_fund_proportion<=1):
            self.collective_fund_proportion = collective_fund_proportion
            self.partial_transform_to_collective_fund(self.collective_fund_proportion)

    def multiplied(self, factor):
        if factor >0:
            return self.amount*factor

    def added(self, amount):
        return self.amount + amount
            
    def payment_prob(self, x, table, next_payment_time = None):
        dt = math.ceil(self.t) - self.t
        if dt == 0:
            self.t = int(self.t)
        if next_payment_time == None:
            return t_p_x(x, self.t-x, table)
        else:
            return t_p_x(x, self.t-x, table)*t_q_x(self.t, next_payment_time-self.t, table)
        
    def expected_at(self, x, table, interest_rates):
        return self.payment_prob(x, table)*(self.value_at(x, interest_rates))

    def collective_fund_premium(self, updated=True):
        if updated:
            self._collective_fund_premium = Premium(self.t, self.transformed_amount)
        else:
            if self._collective_fund_premium == None:
                self._collective_fund_premium = Premium(self.t, 0)
            else:
                pass
        return self._collective_fund_premium

    def partial_transform_to_collective_fund(self, percent):
        if percent > 1 or percent < 0:
            return None
        self.original()
        self.collective_fund_proportion = percent
        self.transformed_amount = self.collective_fund_proportion*self.amount
        self.amount -= self.transformed_amount
    
    def original(self):
        self.amount = self.original_amount
        self.transformed_amount = 0
        self.collective_fund_proportion = 0
        

class TermLifeInsurance(object):

    def __init__(self, x, term, benefits, interest_rates, table):
        self.x = math.floor(x)
        self.t_start = self.x
        self.term = math.floor(term)
        self.t_end = self.x + self.term
        self.table = table
        self.benefits = benefits
        self.interest_rates = interest_rates
        self.adjustments()
        
    def adjustments(self):
        benefits = []; 
        for i in range(len(self.benefits)):
            if (self.x < self.benefits[i].t <= self.t_end):
                benefits.append( self.benefits[i] )
        self.benefits = benefits
        self.benefits = sorted(self.benefits, key = lambda x: x.t)

        int_rates = []; t_taken = []
        for i in range(len(self.interest_rates)):
            if self.interest_rates[i].t not in t_taken:
                int_rates.append( self.interest_rates[i] )
                t_taken.append(self.interest_rates[i].t)
        self.interest_rates = int_rates
        if 0 not in t_taken:
            self.interest_rates[0].t = 0
        self.interest_rates = sorted(self.interest_rates, key = lambda x: x.t)

    def expected_expense(self, t_end):
        if t_end < self.x:
            return 0
        else:
            benefits = [b for b in self.benefits \
                        if self.x <= b.t <= t_end]
            return {'t': [b.t for b in benefits], \
                    'amount': [b.amount for b in benefits], \
                    'probability': [b.claim_prob(self.x, self.table) for b in benefits], \
                    'object': benefits, \
                    'expected': [b.amount*b.claim_prob(self.x, self.table) for b in benefits] \
                    }

    def expected_expense_df(self, t_end):
        expense = self.expected_expense(t_end)
        expected_expense = {}
        t=expense["t"]
        for i in range(len(t)):
            if t[i] not in expected_expense.keys():
                expected_expense[t[i]] = expense["expected"][i]
            else:
                expected_expense[t[i]] = expected_expense[t[i]] + expense["expected"][i]
        t = sorted(expected_expense.keys()); expense = [expected_expense[i] for i in t]
        expense_df = pandas.DataFrame([(i,j) for i,j in zip(t, expense)], columns = ["t", "expense"])
        return expense_df

    def acc_expected_expense(self, t_end, interest_rates):
        if t_end < self.x:
            return 0
        else:
            expected_expense = self.expected_expense(t_end)
            n = len(expected_expense['t'])
            return sum([expected_expense['probability'][i]*expected_expense['object'][i].accumulate(t_end, interest_rates) \
                        for i in range(n)])
        
    def calculate_apv(self, point = "issue"):
        if point == "issue" or point < self.x:
            point = self.x
        return sum([b.expected_at(point, self.table, self.interest_rates) for b in self.benefits])

    def minimum_level_premium(self, annuity = 'immediate', interval = "annual", point = "issue"):
        if point == "issue":
            point = self.x
        exp = []
        if interval == "annual":
            dt = 1
        elif interval == "semi-annual":
            dt = 1/2
        elif interval == "quarter":
            dt = 1/4
        elif interval == "month":
            dt = 1/12
        n_payments = round((self.t_end - point)/dt)
        if annuity == 'immediate':
            for t in range(1, n_payments+1):
                payments =  [Premium(point+dt*(i+1), 1) for i in range(t)]
                payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
                if t==n_payments:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = point+dt*(t+1)))
        elif annuity == 'due':
            for t in range(1, n_payments+1):
                payments =  [Premium(point + dt*i, 1) for i in range(t)]
                payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
                if t==n_payments:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = point+dt*t))
        EXP = sum(exp)
        return self.calculate_apv(point)/EXP


class PureEndowmentInsurance(object):

    def __init__(self, x, term, benefit_amount, interest_rates, table):
        self.x = math.floor(x)
        self.t_start = self.x
        self.term = math.floor(term)
        self.t_end = self.x + self.term
        self.table = table
        self.benefit = [Benefit(self.t_end, benefit_amount, endowment=True)]
        self.interest_rates = interest_rates
        self.adjustments()
        
    def adjustments(self):
        int_rates = []; t_taken = []
        for i in range(len(self.interest_rates)):
            if self.interest_rates[i].t not in t_taken:
                int_rates.append( self.interest_rates[i] )
                t_taken.append(self.interest_rates[i].t)
        self.interest_rates = int_rates
        if 0 not in t_taken:
            self.interest_rates[0].t = 0
        self.interest_rates = sorted(self.interest_rates, key = lambda x: x.t)

    def expected_expense(self, t_end):
        if t_end < self.x:
            return 0
        else:
            benefit = [b for b in self.benefit \
                        if self.x <= b.t <= t_end]
            return {'t': [b.t for b in benefit], \
                    'amount': [b.amount for b in benefit], \
                    'probability': [b.claim_prob(self.x, self.table) for b in benefit], \
                    'object': benefit, \
                    'expected': [b.amount*b.claim_prob(self.x, self.table) for b in benefit] \
                    }

    def expected_expense_df(self, t_end):
        expense = self.expected_expense(t_end)
        expected_expense = {}
        t = expense["t"]
        for i in range(len(t)):
            if t[i] not in expected_expense.keys():
                expected_expense[t[i]] = expense["expected"][i]
            else:
                expected_expense[t[i]] = expected_expense[t[i]] + expense["expected"][i]
        t = sorted(expected_expense.keys()); expense = [expected_expense[i] for i in t]
        expense_df = pandas.DataFrame([(i,j) for i,j in zip(t, expense)], columns = ["t", "expense"])
        return expense_df

    def acc_expected_expense(self, t_end, interest_rates):
        if t_end < self.x:
            return 0
        else:
            expected_expense = self.expected_expense(t_end)
            n = len(expected_expense['t'])
            return sum([expected_expense['probability'][i]*expected_expense['object'][i].accumulate(t_end, interest_rates) \
                        for i in range(n)])
        
    def calculate_apv(self, point = "issue"):
        if point == "issue" or point < self.x:
            point = self.x
        return self.benefit[0].expected_at(point, self.table, self.interest_rates)

    def minimum_level_premium(self, annuity = 'immediate', interval = "annual", point = "issue"):
        if point == "issue":
            point = self.x
        exp = []
        if interval == "annual":
            dt = 1
        elif interval == "semi-annual":
            dt = 1/2
        elif interval == "quarter":
            dt = 1/4
        elif interval == "month":
            dt = 1/12
        n_payments = round((self.t_end - point)/dt)
        if annuity == 'immediate':
            for t in range(1, n_payments+1):
                payments =  [Premium(point+dt*(i+1), 1) for i in range(t)]
                payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
                if t==n_payments:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = point+dt*(t+1)))
        elif annuity == 'due':
            for t in range(1, n_payments+1):
                payments =  [Premium(point + dt*i, 1) for i in range(t)]
                payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
                if t==n_payments:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = point+dt*t))
        EXP = sum(exp)
        return self.calculate_apv(point)/EXP


class EndowmentInsurance(object):

    def __init__(self, x, term, term_benefits, pure_endowment_amount, interest_rates, table):
        self.x = math.floor(x)
        self.t_start = self.x
        self.term = math.floor(term)
        self.t_end = self.x + self.term
        self.table = table
        self.term_benefits = term_benefits
        self.term_life = TermLifeInsurance(self.x, self.term, self.term_benefits, interest_rates, table)
        self.pure_endowment_benefit = [Benefit(self.t_end, pure_endowment_amount, endowment=True)]
        self.benefits = self.term_benefits + self.pure_endowment_benefit
        self.interest_rates = interest_rates
        self.adjustments()
        
    def adjustments(self):
        benefits = []; 
        for i in range(len(self.benefits)):
            if (self.x < self.benefits[i].t <= self.t_end):
                benefits.append( self.benefits[i] )
        self.benefits = benefits
        self.benefits = sorted(self.benefits[0:-1], key = lambda x: x.t)+[self.benefits[-1]]

        int_rates = []; t_taken = []
        for i in range(len(self.interest_rates)):
            if self.interest_rates[i].t not in t_taken:
                int_rates.append( self.interest_rates[i] )
                t_taken.append(self.interest_rates[i].t)
        self.interest_rates = int_rates
        if 0 not in t_taken:
            self.interest_rates[0].t = 0
        self.interest_rates = sorted(self.interest_rates, key = lambda x: x.t)

    def expected_expense(self, t_end):
        if t_end < self.x:
            return 0
        else:
            benefits = [b for b in self.benefits \
                        if self.x <= b.t <= t_end]
            return {'t': [b.t for b in benefits], \
                    'amount': [b.amount for b in benefits], \
                    'probability': [b.claim_prob(self.x, self.table) for b in benefits], \
                    'object': benefits, \
                    'expected': [b.amount*b.claim_prob(self.x, self.table) for b in benefits] \
                    }

    def expected_expense_df(self, t_end):
        expense = self.expected_expense(t_end)
        expected_expense = {}
        t=expense["t"]
        for i in range(len(t)):
            if t[i] not in expected_expense.keys():
                expected_expense[t[i]] = expense["expected"][i]
            else:
                expected_expense[t[i]] = expected_expense[t[i]] + expense["expected"][i]
        t = sorted(expected_expense.keys()); expense = [expected_expense[i] for i in t]
        expense_df = pandas.DataFrame([(i,j) for i,j in zip(t, expense)], columns = ["t", "expense"])
        return expense_df

    def acc_expected_expense(self, t_end, interest_rates):
        if t_end < self.x:
            return 0
        else:
            expected_expense = self.expected_expense(t_end)
            n = len(expected_expense['t'])
            return sum([expected_expense['probability'][i]*expected_expense['object'][i].accumulate(t_end, interest_rates) \
                        for i in range(n)])
        
    def calculate_apv(self, point = "issue"):
        if point == "issue" or point < self.x:
            point = self.x
        return sum([b.expected_at(point, self.table, self.interest_rates) for b in self.benefits])

    def minimum_level_premium(self, annuity = 'immediate', interval = "annual", point = "issue"):
        if point == "issue":
            point = self.x
        exp = []
        if interval == "annual":
            dt = 1
        elif interval == "semi-annual":
            dt = 1/2
        elif interval == "quarter":
            dt = 1/4
        elif interval == "month":
            dt = 1/12
        n_payments = round((self.t_end - point)/dt)
        if annuity == 'immediate':
            for t in range(1, n_payments+1):
                payments =  [Premium(point+dt*(i+1), 1) for i in range(t)]
                payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
                if t==n_payments:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = point+dt*(t+1)))
        elif annuity == 'due':
            for t in range(1, n_payments+1):
                payments =  [Premium(point + dt*i, 1) for i in range(t)]
                payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
                if t==n_payments:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = point+dt*t))
        EXP = sum(exp)
        return self.calculate_apv(point)/EXP
    

class TermLifeAnnuity(object):

    def __init__(self, x, term, payments, interest_rates, table):
        self.x = math.floor(x)
        self.t_start = self.x
        self.term = math.floor(term)
        self.table = table
        self.payments = payments
        self.interest_rates = interest_rates
        self.adjustments()
        
    def adjustments(self):
        payments = []; 
        for i in range(len(self.payments)):
            if (self.x <= self.payments[i].t <= self.x + self.term):
                payments.append( self.payments[i] )
        self.payments = payments
        self.payments = sorted(self.payments, key = lambda x: x.t)

        int_rates = []; t_taken = []
        for i in range(len(self.interest_rates)):
            if self.interest_rates[i].t not in t_taken:
                int_rates.append( self.interest_rates[i] )
                t_taken.append(self.interest_rates[i].t)
        self.interest_rates = int_rates
        if 0 not in t_taken:
            self.interest_rates[0].t = 0
        self.interest_rates = sorted(self.interest_rates, key = lambda x: x.t)

    def expected_payments(self, t_end):
        if t_end < self.x:
            return 0
        else:
            payments = [p for p in self.payments \
                        if self.x <= p.t <= t_end]
            return {'t': [p.t for p in payments], \
                    'amount': [p.amount for p in payments], \
                    'probability': [p.payment_prob(self.x, self.table) for p in payments], \
                    'object': payments, \
                    'expected': [p.amount*p.payment_prob(self.x, self.table) for p in payments] \
                    }

    def expected_payments_df(self, t_end):
        payment = self.expected_payments(t_end)
        expected_payment = {}
        t=payment["t"]
        for i in range(len(t)):
            if t[i] not in expected_payment.keys():
                expected_payment[t[i]] = payment["expected"][i]
            else:
                expected_payment[t[i]] = expected_payment[t[i]] + payment["expected"][i]
        t = sorted(expected_payment.keys()); payment = [expected_payment[i] for i in t]
        payment_df = pandas.DataFrame([(i,j) for i,j in zip(t, payment)], columns = ["t", "income"])
        return payment_df

    def acc_expected_payments(self, t_end, interest_rates):
        if t_end < self.x:
            return 0
        else:
            expected_payments = self.expected_payments(t_end)
            n = len(expected_payments['t'])
            return sum([expected_payments['probability'][i]*expected_payments['object'][i].accumulate(t_end, interest_rates) \
                        for i in range(n)])
            
    def calculate_apv(self, point = "issue"):
        if point == "issue" or point < self.x:
            point = self.x
        exp = []
        np = len(self.payments)
        for i in range(np):
            if self.payments[i].t < point:
                continue
            payments = [p for p in self.payments[0:(i+1)] if point <= p.t]
            payments_pv = sum([p.value_at(point, self.interest_rates) for p in payments])
            if len(payments) > 0:
                if i < np - 1:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table, next_payment_time = self.payments[i+1].t))
                else:
                    exp.append(payments_pv*payments[-1].payment_prob(point, self.table))
        return sum(exp)


class ActuarialModel(object):

    def __init__(self, insurance, annuity, policy_year, policy_month=1):
        self.insurance = insurance
        self.x = self.insurance.x
        self.term = self.insurance.term
        self.table = self.insurance.table
        self.interest_rates = self.insurance.interest_rates
        self.policy_year = int(max(0, policy_year))
        self.policy_month = int(max(1, min(policy_month, 12)))
        self.t_policy = self.policy_year + self.policy_month/12
        if annuity[1] == "annual":
            dt = 1
        elif annuity[1] == "semi-annual":
            dt = 1/2
        elif annuity[1] == "quarter":
            dt = 1/4
        elif annuity[1] == "month":
            dt = 1/12
        n_payments = round((self.insurance.term)/dt)
        if annuity[0] == "immediate":
            premium = self.insurance.minimum_level_premium(annuity = "immediate", interval = annuity[1])
            self.annuity = TermLifeAnnuity(self.insurance.x, self.insurance.term, \
                                           [Premium(self.insurance.x + (i+1)*dt, premium) for i in range(n_payments)], \
                                           self.insurance.interest_rates, \
                                           self.insurance.table)
        elif annuity[0] == "due":
            premium = self.insurance.minimum_level_premium(annuity = "due", interval = annuity[1])
            self.annuity = TermLifeAnnuity(self.insurance.x, self.insurance.term, \
                                           [Premium(self.insurance.x + (i)*dt, premium) for i in range(n_payments)], \
                                           self.insurance.interest_rates, \
                                           self.insurance.table)
        elif type(annuity) != list:
            self.annuity = annuity

    def income_expense(self, t_end):
        income = self.annuity.expected_payments(t_end)
        expense = self.insurance.expected_expense(t_end)
        return income, expense

    def income_expense_df(self, t_end):
        income_df = self.annuity.expected_payments_df(t_end)
        expense_df = self.insurance.expected_expense_df(t_end)
        return income_df, expense_df

    def cashflow_df(self, t_end, frequency_weight = 1, collective_interest_rates = None):
        income_df, expense_df = self.income_expense_df(t_end)
        if (collective_interest_rates == None):
            collective_interest_rates = [fm.InterestRate(0, 0, "annual")]
        collective_premiums = [p.collective_fund_premium(True) for p in self.annuity.payments]
        collective_fund_annuity = TermLifeAnnuity(self.x, self.term, collective_premiums, \
                                                  collective_interest_rates, self.table)        
        collective_fund_annuity_df = collective_fund_annuity.expected_payments_df(t_end)
        return collective_fund_annuity_df
        collective_fund_annuity_df = collective_fund_annuity_df.rename(columns = {'income': 'income_from_collective_fund'})
        df=income_df.merge(expense_df, how='outer', on='t', sort=True)
        df=df.merge(collective_fund_annuity_df, how='outer', on='t', sort=True)
        df=df.fillna(0)

        df.income_from_collective_fund *= frequency_weight
        cashflow = df.income.subtract(df.expense, fill_value=0)
        cashflow_df = pandas.DataFrame([[i,j*frequency_weight] for i,j in zip(df.t, cashflow)], \
                                       columns = ['t', 'profit_exclude_collective_fund'])
                
        cashflow_df = cashflow_df.merge(df, how='outer', on='t', sort=True)
        cashflow_df.fillna(0)
        cashflow_df.income = cashflow_df.income.multiply(frequency_weight)
        cashflow_df.expense = cashflow_df.expense.multiply(frequency_weight)

        exp_contributions = [fm.Contribution(cashflow_df.t[i], cashflow_df.profit_exclude_collective_fund[i]) for i in range(len(cashflow_df))]
        exp_contributions_fund = [fm.Contribution(cashflow_df.t[i], cashflow_df.income_from_collective_fund[i]) for i in range(len(cashflow_df))]

        accumulated = []
        for i in range(1, len(exp_contributions)+1):
            involved = exp_contributions[0:i]
            total = sum([j.accumulate(involved[-1].t, self.interest_rates)  for j in involved])
            accumulated.append(total)

        accumulated_2 = []
        for i in range(1, len(exp_contributions_fund)+1):
            involved = exp_contributions_fund[0:i]
            total = sum([j.accumulate(involved[-1].t, collective_interest_rates)  for j in involved])
            accumulated_2.append(total)
 
        cashflow_df['accumulated_profit_exclude_collective_fund'] = pandas.Series(accumulated, index = cashflow_df.index)
        cashflow_df['accumulated_income_collective_fund'] = pandas.Series(accumulated_2, index = cashflow_df.index)
        cashflow_df['total_accumulated_profit'] = cashflow_df['accumulated_profit_exclude_collective_fund'] + cashflow_df['accumulated_income_collective_fund']

        t_policy = [round(self.t_policy,3)]
        for i in range(len(cashflow_df['t'])-1):
            t_policy.append(round(t_policy[-1] + cashflow_df['t'][i+1]-cashflow_df['t'][i], 3))
        cashflow_df['t_policy'] = pandas.Series(t_policy, index = cashflow_df.index)
        cols = list(cashflow_df.columns)
        cols.insert(1, cols.pop())
        cashflow_df = cashflow_df.reindex(columns=cols)
        return cashflow_df

    def reserves_at(self, t):
        return self.insurance.calculate_apv(point = t) - self.annuity.calculate_apv(point = t)

    def reserves_dynamics(self, dt, t_end):
        N = math.floor((t_end-self.insurance.x)/dt)
        t = [self.insurance.x + dt*i for i in range(N+1)]
        if t[-1]!=t_end:
            t.append(t_end)
        reserves = [self.reserves_at(i) for i in t]
        return t, reserves
    
    def reserves_dynamics_df(self, dt, t_end):
        t, reserves = self.reserves_dynamics(dt, t_end)
        df = pandas.DataFrame(data = [[i,j] for i,j in zip(t, reserves)], \
                              columns = ["t", "Reserves"])
        return df
