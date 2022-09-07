import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from pandas_datareader import data
from datetime import timedelta, date
import numpy_financial as npf
import yfinance as yf

def dcf_and_lereved(ticker, negara):
    #URL
    url_financials_is = 'https://finance.yahoo.com/quote/{}/financials?p={}'
    url_financials_fcf = 'https://finance.yahoo.com/quote/{}/cash-flow?p={}'
    url_balenceSheet = 'https://finance.yahoo.com/quote/{}/balance-sheet?p={}'

    #Variable
    ticker_code = ticker
    negara = negara
    if negara == 'indonesia':
        ticker_code = ticker_code + '.JK'

    #headers
    headers = { 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36' }
    response = requests.get(url_financials_is.format(ticker_code, ticker_code),headers={'user-agent':'my-app'})
    response_fcf = requests.get(url_financials_fcf.format(ticker_code, ticker_code),headers={'user-agent':'my-app'})
    response_bs = requests.get(url_balenceSheet.format(ticker_code, ticker_code),headers={'user-agent':'my-app'})


    #scriping
    soup = BeautifulSoup(response.text, 'html.parser')
    pattern = re.compile(r'\s--\sData\s--\s')
    script_data = soup.find('script', text=pattern).contents[0]
    start = script_data.find("context")-2
    json_data = json.loads(script_data[start:-12])

    soup_fcf = BeautifulSoup(response_fcf.text, 'html.parser')
    script_data_fcf =  soup_fcf.find('script', text=pattern).contents[0]
    start_fcf = script_data_fcf.find("context")-2
    json_data_fcf = json.loads(script_data_fcf[start_fcf:-12])

    soup_bs = BeautifulSoup(response_bs.text, 'html.parser')
    pattern_bs = re.compile(r'\s--\sData\s--\s')
    script_data_bs = soup_bs.find('script', text=pattern_bs).contents[0]
    start_bs = script_data_bs.find("context")-2
    json_data_bs = json.loads(script_data_bs[start:-12])


    #location variable of yahoo
    I_S_start = json_data['context']['dispatcher']['stores']
    fcf_start = json_data_fcf['context']['dispatcher']['stores']
    B_S_start = json_data_bs['context']['dispatcher']['stores']

    def date_is_annual(input1, I_S_start, ticker_code):
        if input1 == 'lastyear':
            year = 0
            input2 = -1
        elif input1 == 'yearago':
            year = 1
            input2 = -2
        elif input1 ==  'years2ago':
            year = 2
            input2 = -3
        elif input1 ==  'years3ago':
            year = 3
            input2 = -4
        elif input1 ==  'years4ago':
            year = 4
            input2 = -5
        else:
            print('out of index')
        #old
        date = I_S_start['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][year]['endDate']['fmt']
        ###reportedCurrency = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualOperatingExpense'][input2]['currencyCode']
        revenue = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualTotalRevenue'][input2]['reportedValue']['raw']
        try:
            EBITDA = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualNormalizedEBITDA'][input2]['reportedValue']['raw']
        except:
            EBITDA = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualReconciledDepreciation'][input2]['reportedValue']['raw'] + I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualInterestExpense'][input2]['reportedValue']['raw'] + I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualPretaxIncome'][input2]['reportedValue']['raw'] + I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualMinorityInterests'][input2]['reportedValue']['raw']
            
        depreciation = I_S_start['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][year]['depreciation']['raw']
        ebitda_persen = EBITDA/revenue
        ebit = EBITDA - depreciation
        ebit_persen = ((EBITDA - depreciation)/revenue)
        depreciation_persen = ebitda_persen - ebit_persen
        
        
        
        
        #variable
        date = date
        income_statement = {}
        income_statement[input1] = {}
        income_statement[input1]['revenue'] = revenue
        income_statement[input1]['EBITDA'] = EBITDA
        income_statement[input1]['EBITDA(%)'] = ebitda_persen
        income_statement[input1]['Ebit'] = ebit
        income_statement[input1]['Ebit(%)'] = ebit_persen
        income_statement[input1]['Depreciation'] = depreciation
        income_statement[input1]['Depreciation(%)'] = depreciation_persen
        
        return income_statement
    
    income_statement_3 = date_is_annual('lastyear', I_S_start, ticker_code)
    income_statement_2 = date_is_annual('yearago', I_S_start, ticker_code)
    income_statement_1 = date_is_annual('years2ago', I_S_start, ticker_code)

    cagr_revenue = ((income_statement_3['lastyear']['revenue']/income_statement_1['years2ago']['revenue'])**(1/3)-1)

    revenue4 = (income_statement_3['lastyear']['revenue']*cagr_revenue) + income_statement_3['lastyear']['revenue']
    revenue5 = (revenue4*cagr_revenue) + revenue4
    revenue6 = (revenue5*cagr_revenue) + revenue5
    revenue7 = (revenue6*cagr_revenue) + revenue6

    ebitda3_persen = income_statement_3['lastyear']['EBITDA(%)']
    ebitda2_persen = income_statement_2['yearago']['EBITDA(%)']
    ebitda1_persen = income_statement_1['years2ago']['EBITDA(%)']

    rata2ebitda = (ebitda1_persen + ebitda2_persen + ebitda3_persen)/3

    ebitda3 = income_statement_3['lastyear']['EBITDA']
    ebitda2= income_statement_2['yearago']['EBITDA']
    ebitda1 = income_statement_1['years2ago']['EBITDA']
    ebitda4 = revenue4 * rata2ebitda
    ebitda5 = revenue5 * rata2ebitda
    ebitda6 = revenue6 * rata2ebitda

    ebit3_persen = income_statement_3['lastyear']['Ebit(%)']
    ebit2_persen = income_statement_2['yearago']['Ebit(%)']
    ebit1_persen = income_statement_1['years2ago']['Ebit(%)']
    rata2ebit = (ebit1_persen + ebit2_persen + ebit3_persen)/3

    rata2Depreciation = rata2ebitda - rata2ebit
    Depreciation4 = revenue4 * rata2Depreciation
    Depreciation5 = revenue5 * rata2Depreciation
    Depreciation6 = revenue6 * rata2Depreciation

    ebit4 = ebitda4 - Depreciation4
    ebit5 = ebitda5 - Depreciation5
    ebit6 = ebitda6 - Depreciation6

    income_statement_4 = {
        'future1': {
            'revenue': revenue4, 
            'EBITDA' : ebitda4, 
            'EBITDA(%)' : rata2ebitda, 
            'Ebit' : ebit4, 
            'Ebit(%)' : rata2ebit, 
            'Depreciation' : Depreciation4, 
            'Depreciation(%)' : rata2Depreciation
        }
    }

    income_statement_5 = {
        'future2': {
            'revenue': revenue5, 
            'EBITDA' : ebitda5, 
            'EBITDA(%)' : rata2ebitda, 
            'Ebit' : ebit5, 
            'Ebit(%)' : rata2ebit, 
            'Depreciation' : Depreciation5, 
            'Depreciation(%)' : rata2Depreciation
        }
    }

    income_statement_6 = {
        'future3': {
            'revenue': revenue6, 
            'EBITDA' : ebitda6, 
            'EBITDA(%)' : rata2ebitda, 
            'Ebit' : ebit6, 
            'Ebit(%)' : rata2ebit, 
            'Depreciation' : Depreciation6, 
            'Depreciation(%)' : rata2Depreciation
        }
    }

    income_statement = income_statement_1 | income_statement_2 | income_statement_3 | income_statement_4 | income_statement_5 | income_statement_6
    income_statement = pd.DataFrame.from_dict(income_statement,orient='columns')
    income_statement

    def date_bs_annual(input1, B_S_start, income_statement, ticker_code):
        if input1 == 'lastyear':
            year = 0
            input2 = -1
        elif input1 == 'yearago':
            year = 1
            input2 = -2
        elif input1 ==  'years2ago':
            year = 2
            input2 = -3
        elif input1 ==  'years3ago':
            year = 3
            input2 = -4
        elif input1 ==  'years4ago':
            year = 4
            input2 = -5
        else:
            print('out of index')
        
        try:
            total_cash = B_S_start['QuoteTimeSeriesStore']['timeSeries']['annualCashCashEquivalentsAndShortTermInvestments'][input2]['reportedValue']['raw']
        except:
            total_cash = B_S_start['QuoteTimeSeriesStore']['timeSeries']['annualCashAndCashEquivalents'][input2]['reportedValue']['raw']
        revenue =  income_statement[input1]['revenue']
        account_receivables = B_S_start['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][year]['netReceivables']['raw']
        inventories = B_S_start['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][year]['inventory']['raw']
        accountsPayable = B_S_start['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements'][year]['accountsPayable']['raw']
        capitalExpenditure = B_S_start['QuoteSummaryStore']['cashflowStatementHistory']['cashflowStatements'][year]['capitalExpenditures']['raw']

        
        balance_sheet = {}
        balance_sheet[input1] = {}
        balance_sheet[input1]['Total Cash'] = total_cash
        balance_sheet[input1]['Total Cash(%)'] = total_cash / revenue
        balance_sheet[input1]['account receivables'] = account_receivables
        balance_sheet[input1]['account receivables(%)'] = account_receivables / revenue
        balance_sheet[input1]['Inventories'] = inventories
        balance_sheet[input1]['Inventories(%)'] = inventories / revenue
        balance_sheet[input1]['accounts Payable'] = accountsPayable
        balance_sheet[input1]['accounts Payable(%)'] = accountsPayable / revenue
        balance_sheet[input1]['capital Expenditure'] = capitalExpenditure
        balance_sheet[input1]['capital Expenditure(%)'] = capitalExpenditure / revenue
        
        return balance_sheet

    bs1 = date_bs_annual('years2ago', B_S_start, income_statement, ticker_code)
    bs2 = date_bs_annual('yearago', B_S_start, income_statement, ticker_code)
    bs3 = date_bs_annual('lastyear', B_S_start, income_statement, ticker_code)

    cash1_persen = bs1['years2ago']['Total Cash(%)']
    cash2_persen = bs2['yearago']['Total Cash(%)']
    cash3_persen = bs3['lastyear']['Total Cash(%)']
    rata2cash = (cash1_persen + cash2_persen + cash3_persen)/3

    cash4 = revenue4 * rata2cash
    cash5 = revenue5 * rata2cash
    cash6 = revenue6 * rata2cash

    account_receivables_1_persen = bs1['years2ago']['account receivables(%)']
    account_receivables_2_persen = bs2['yearago']['account receivables(%)']
    account_receivables_3_persen = bs3['lastyear']['account receivables(%)']
    rata_AR_cash = (account_receivables_1_persen + account_receivables_2_persen + account_receivables_3_persen)/3

    account_receivables4 = revenue4 * rata_AR_cash
    account_receivables5 = revenue5 * rata_AR_cash
    account_receivables6 = revenue6 * rata_AR_cash
    account_receivables7 = revenue7 * rata_AR_cash

    Inventories1_persen = bs1['years2ago']['Inventories(%)']
    Inventories2_persen = bs2['yearago']['Inventories(%)']
    Inventories3_persen = bs3['lastyear']['Inventories(%)']
    rata_Inventories = (Inventories1_persen + Inventories2_persen + Inventories3_persen)/3

    inventories4 = revenue4 * rata_Inventories
    inventories5 = revenue5 * rata_Inventories
    inventories6 = revenue6 * rata_Inventories

    account_Payable_1_persen = bs1['years2ago']['accounts Payable(%)']
    account_Payable_2_persen = bs2['yearago']['accounts Payable(%)']
    account_Payable_3_persen = bs3['lastyear']['accounts Payable(%)']
    rata_Payable_cash = (account_Payable_1_persen + account_Payable_2_persen + account_Payable_3_persen)/3

    account_Payable_4 = revenue4 * rata_Payable_cash
    account_Payable_5 = revenue5 * rata_Payable_cash
    account_Payable_6 = revenue6 * rata_Payable_cash

    capital_Expenditure_1_persen = bs1['years2ago']['capital Expenditure(%)']
    capital_Expenditure_2_persen = bs2['yearago']['capital Expenditure(%)']
    capital_Expenditure_3_persen = bs3['lastyear']['capital Expenditure(%)']
    rata_CE_cash = (capital_Expenditure_1_persen + capital_Expenditure_2_persen + capital_Expenditure_3_persen)/3

    capital_Expenditure_4 = revenue4 * rata_CE_cash
    capital_Expenditure_5 = revenue5 * rata_CE_cash
    capital_Expenditure_6 = revenue6 * rata_CE_cash

    bs4 = {
        'future1' : {
            'Total Cash': cash4, 
            'Total Cash(%)': rata2cash, 
            'account receivables' : account_receivables4, 
            'account receivables(%)' : rata_AR_cash, 
            'Inventories' : inventories4, 
            'Inventories(%)' : rata_Inventories, 
            'accounts Payable' : account_Payable_4, 
            'accounts Payable(%)' : rata_Payable_cash, 
            'capital Expenditure' : capital_Expenditure_4, 
            'capital Expenditure(%)' : rata_CE_cash 
        }
    }

    bs5 = {
        'future2' : {
            'Total Cash': cash5, 
            'Total Cash(%)': rata2cash, 
            'account receivables' : account_receivables5, 
            'account receivables(%)' : rata_AR_cash, 
            'Inventories' : inventories5, 
            'Inventories(%)' : rata_Inventories, 
            'accounts Payable' : account_Payable_5, 
            'accounts Payable(%)' : rata_Payable_cash, 
            'capital Expenditure' : capital_Expenditure_5, 
            'capital Expenditure(%)' : rata_CE_cash 
        }
    }

    bs6 = {
        'future3' : {
            'Total Cash': cash6, 
            'Total Cash(%)': rata2cash, 
            'account receivables' : account_receivables6, 
            'account receivables(%)' : rata_AR_cash, 
            'Inventories' : inventories6, 
            'Inventories(%)' : rata_Inventories, 
            'accounts Payable' : account_Payable_6, 
            'accounts Payable(%)' : rata_Payable_cash, 
            'capital Expenditure' : capital_Expenditure_6, 
            'capital Expenditure(%)' : rata_CE_cash 
        }
    }

    balance_sheet = bs1 | bs2 | bs3 | bs4 | bs5 | bs6
    balance_sheet = pd.DataFrame.from_dict(balance_sheet,orient='columns')

    input_ticker = yf.Ticker(ticker_code)
    info_ticker = input_ticker.info

    #Weighted Average Cost Of Capital
    share_price = info_ticker['regularMarketPrice']
    beta = info_ticker['beta']
    diluted_Shares_Outstanding = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualDilutedAverageShares'][-1]['reportedValue']['raw']
    #tax_Rate = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualTaxRateForCalcs'][-1]['reportedValue']['raw']#*100
    interestExpense = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualInterestExpense'][-1]['reportedValue']['raw']
    totalDebt = B_S_start['QuoteTimeSeriesStore']['timeSeries']['annualTotalDebt'][-1]['reportedValue']['raw']
    incomeTaxExp = I_S_start['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][0]['incomeTaxExpense']['raw']
    incomeBeforeTax = I_S_start['QuoteSummaryStore']['incomeStatementHistory']['incomeStatementHistory'][0]['incomeBeforeTax']['raw']
    riskFreeRate = I_S_start['StreamDataStore']['quoteData']['^TNX']['regularMarketPrice']['raw']


    wacc = {}
    wacc['Share Price'] = share_price
    wacc['beta'] = beta
    wacc['Diluted Shares Outstanding'] = diluted_Shares_Outstanding
    #wacc['Tax Rate'] = tax_Rate
    wacc['costOfDebt'] =  interestExpense/totalDebt
    wacc['TaxRate'] = incomeTaxExp/incomeBeforeTax
    wacc['After_tax_CostOfDebt'] = wacc['costOfDebt'] * (1 - wacc['TaxRate'])
    if negara == 'indonesia':
        wacc['riskFreeRate'] = 5.5
    else:
        wacc['riskFreeRate'] = riskFreeRate
    wacc['marketriskpremium'] = 4.72
    wacc['totaldebt'] = totalDebt
    wacc['costofequity'] = wacc['riskFreeRate'] + (wacc['beta'] * wacc['marketriskpremium'])
    wacc['totalequity'] = wacc['Share Price'] * wacc['Diluted Shares Outstanding']
    wacc['totalcapital'] = wacc['totalequity'] + wacc['totaldebt']
    wacc['DebtWeighting'] = (wacc['totaldebt'] / wacc['totalcapital'])*100
    wacc['EquityWeighting'] = (wacc['totalequity'] / wacc['totalcapital'])*100
    wacc['WACC'] = (wacc['EquityWeighting'] * wacc['costofequity'] + wacc['DebtWeighting'] * wacc['After_tax_CostOfDebt'])/100

    table_wacc = pd.DataFrame.from_dict(wacc,orient='index')

    pretaxIncome = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualPretaxIncome']
    TaxProvision = I_S_start['QuoteTimeSeriesStore']['timeSeries']['annualTaxProvision']

    pretaxIncome_freecash_last = pretaxIncome[-1]['reportedValue']['raw']
    TaxProvision_freecash_last = TaxProvision[-1]['reportedValue']['raw']
    TaxRate_freecash_last = TaxProvision_freecash_last/pretaxIncome_freecash_last

    pretaxIncome_freecash_1ago = pretaxIncome[-2]['reportedValue']['raw']
    TaxProvision_freecash_1ago = TaxProvision[-2]['reportedValue']['raw']
    TaxRate_freecash_1ago = TaxProvision_freecash_1ago/pretaxIncome_freecash_1ago

    pretaxIncome_freecash_2ago = pretaxIncome[-3]['reportedValue']['raw']
    TaxProvision_freecash_2ago = TaxProvision[-3]['reportedValue']['raw']
    TaxRate_freecash_2ago = TaxProvision_freecash_2ago/pretaxIncome_freecash_2ago

    taxRate_future = (TaxRate_freecash_last + TaxRate_freecash_1ago + TaxRate_freecash_2ago)/3

    #Receivables = B_S_start['QuoteSummaryStore']['balanceSheetHistory']['balanceSheetStatements']
    Receivables_freecash_1ago = balance_sheet['years2ago']['account receivables'] - balance_sheet['yearago']['account receivables'] #2019-2020
    Receivables_freecash_last = balance_sheet['yearago']['account receivables'] - balance_sheet['lastyear']['account receivables'] #2020-2021

    Receivables_future1 = balance_sheet['lastyear']['account receivables'] - balance_sheet['future1']['account receivables'] #2021-2022
    Receivables_future2 = balance_sheet['future1']['account receivables'] - balance_sheet['future2']['account receivables'] #2022-2023
    Receivables_future3 = balance_sheet['future2']['account receivables'] - balance_sheet['future3']['account receivables']

    #====
    ebiat_freecash_2ago = income_statement['years2ago']['Ebit']*(1-TaxRate_freecash_2ago)
    ebiat_freecash_1ago = income_statement['yearago']['Ebit']*(1-TaxRate_freecash_1ago)
    ebiat_freecash_last = income_statement['lastyear']['Ebit']*(1-TaxRate_freecash_last)
    ebiat_freecash_future1 = ebit4*(1-(taxRate_future))
    ebiat_freecash_future2 = ebit5*(1-(taxRate_future))
    ebiat_freecash_future3 = ebit6*(1-(taxRate_future))

    #====
    depreciation_freecash_2ago = income_statement['years2ago']['Depreciation']
    depreciation_year1ago = income_statement['yearago']['Depreciation']
    depreciation_last = income_statement['lastyear']['Depreciation']
    depreciation_future1 = income_statement['future1']['Depreciation']
    depreciation_future2 = income_statement['future2']['Depreciation']
    depreciation_future3 = income_statement['future3']['Depreciation']


    #====
    inventories_freecash_last = balance_sheet['yearago']['Inventories'] - balance_sheet['lastyear']['Inventories']
    inventories_freecash_1ago = balance_sheet['years2ago']['Inventories'] - balance_sheet['yearago']['Inventories']
    inventories_future1 = balance_sheet['lastyear']['Inventories'] - balance_sheet['future1']['Inventories']
    inventories_future2 = balance_sheet['future1']['Inventories'] - balance_sheet['future2']['Inventories']
    inventories_future3 = balance_sheet['future2']['Inventories'] - balance_sheet['future3']['Inventories']

    #=====
    accountsPayable_freecash_1ago = balance_sheet['yearago']['accounts Payable'] - balance_sheet['years2ago']['accounts Payable']
    accountsPayable_freecash_last = balance_sheet['lastyear']['accounts Payable'] - balance_sheet['yearago']['accounts Payable']
    accountsPayable_future1 = balance_sheet['future1']['accounts Payable'] - balance_sheet['lastyear']['accounts Payable']
    accountsPayable_future2 = balance_sheet['future2']['accounts Payable'] - balance_sheet['future1']['accounts Payable']
    accountsPayable_future3 = balance_sheet['future3']['accounts Payable'] - balance_sheet['future2']['accounts Payable']

    #====
    capitalExpenditure_freecash_2ago = balance_sheet['years2ago']['capital Expenditure']
    capitalExpenditure_freecash_1ago = balance_sheet['yearago']['capital Expenditure']
    capitalExpenditure_freecash_last = balance_sheet['lastyear']['capital Expenditure']

    #UFCF
    ufcf_2ago = ebiat_freecash_2ago + depreciation_freecash_2ago + capitalExpenditure_freecash_2ago
    ufcf_1ago = ebiat_freecash_1ago + depreciation_year1ago + Receivables_freecash_1ago + inventories_freecash_1ago + accountsPayable_freecash_1ago + capitalExpenditure_freecash_1ago
    ufcf_last = ebiat_freecash_last + depreciation_last + Receivables_freecash_last + inventories_freecash_last + accountsPayable_freecash_last + capitalExpenditure_freecash_last
    ufcf_future1 = ebiat_freecash_future1 + depreciation_future1 + Receivables_future1 + inventories_future1 + accountsPayable_future1 + capital_Expenditure_4
    ufcf_future2 = ebiat_freecash_future2 + depreciation_future2 + Receivables_future2 + inventories_future2 + accountsPayable_future2 + capital_Expenditure_5
    ufcf_future3 = ebiat_freecash_future3 + depreciation_future3 + Receivables_future3 + inventories_future3 + accountsPayable_future3 + capital_Expenditure_5

    #==== PV UFCF ====#
    wacc_pv = table_wacc[0]['WACC']
    pV_ufcf_future1 = ufcf_future1 / (1+(wacc_pv/100))
    pV_ufcf_future2 = ufcf_future2 / (1+(wacc_pv/100))**2
    pV_ufcf_future3 = ufcf_future3 / (1+(wacc_pv/100))**3
    

    freecash= {

        'years2ago': {
                        'revenue': income_statement['years2ago']['revenue'],
                        'EBITDA' : income_statement['years2ago']['EBITDA'],
                        'Ebit' : income_statement['years2ago']['Ebit'],
                        'TaxRate': TaxRate_freecash_2ago*100,
                        'EBIAT' : ebiat_freecash_2ago,
                        'Depreciation' : depreciation_freecash_2ago,
                        'AccountsReceivable' : 0,
                        'Inventories' : 0,
                        'accountsPayable' : 0,
                        'Capital Expenditure' : capitalExpenditure_freecash_2ago,
                        'UFCF' : ufcf_2ago,
                    },
        


        'yearago': {
                    'revenue': income_statement['yearago']['revenue'],
                    'EBITDA' : income_statement['yearago']['EBITDA'],
                    'Ebit' : income_statement['yearago']['Ebit'],
                    'TaxRate': TaxRate_freecash_1ago*100,
                    'EBIAT' : ebiat_freecash_1ago,
                    'Depreciation' : depreciation_year1ago,
                    'AccountsReceivable' : Receivables_freecash_1ago,
                    'Inventories' : inventories_freecash_1ago,
                    'accountsPayable' : accountsPayable_freecash_1ago,
                    'Capital Expenditure' : capitalExpenditure_freecash_1ago,
                    'UFCF' : ufcf_1ago
                },
        

        'lastyear': {
                    'revenue': income_statement['lastyear']['revenue'], 
                    'EBITDA' : income_statement['lastyear']['EBITDA'], 
                    'Ebit' : income_statement['lastyear']['Ebit'],
                    'TaxRate': TaxRate_freecash_last*100,
                    'EBIAT' : ebiat_freecash_last,
                    'Depreciation' : depreciation_last,
                    'AccountsReceivable' : Receivables_freecash_last,
                    'Inventories' : inventories_freecash_last,
                    'accountsPayable' : accountsPayable_freecash_last,
                    'Capital Expenditure' : capitalExpenditure_freecash_last,
                    'UFCF' : ufcf_last
                },
        

        'future1': {
                        'revenue': revenue4, 
                        'EBITDA' : ebitda4, 
                        'Ebit' : ebit4,
                        'TaxRate' : taxRate_future*100,
                        'EBIAT' : ebiat_freecash_future1,
                        'Depreciation' : depreciation_future1,
                        'AccountsReceivable' : Receivables_future1,
                        'Inventories' : inventories_future1,
                        'accountsPayable' : accountsPayable_future1,
                        'Capital Expenditure' : capital_Expenditure_4,
                        'UFCF' : ufcf_future1,
                        'PV_UFCF' : pV_ufcf_future1,                        
                    },
        

        'future2': {
                        'revenue': revenue5, 
                        'EBITDA' : ebitda5, 
                        'Ebit' : ebit5,
                        'TaxRate' : taxRate_future*100,
                        'EBIAT' : ebiat_freecash_future2,
                        'Depreciation' : depreciation_future2,
                        'AccountsReceivable' : Receivables_future2,
                        'Inventories' : inventories_future2,
                        'accountsPayable' : accountsPayable_future2,
                        'Capital Expenditure' : capital_Expenditure_5,
                        'UFCF' : ufcf_future2,
                        'PV_UFCF' : pV_ufcf_future2,
                        
                    },
        

        'future3': {
                        'revenue': revenue6, 
                        'EBITDA' : ebitda6, 
                        'Ebit' : ebit6,
                        'TaxRate' : taxRate_future*100,
                        'EBIAT' : ebiat_freecash_future3,
                        'Depreciation' : depreciation_future3,
                        'AccountsReceivable' : Receivables_future3,
                        'Inventories' : inventories_future3,
                        'accountsPayable' : accountsPayable_future3,
                        'Capital Expenditure' : capital_Expenditure_5,
                        'UFCF' : ufcf_future3,
                        'PV_UFCF' : pV_ufcf_future3,
                            
                    }


    }

    freecash = pd.DataFrame.from_dict(freecash,orient='columns')
    #ada perbedaan di AccountsReceivable

    sum_pv_ufcf = pV_ufcf_future1 + pV_ufcf_future2 + pV_ufcf_future3

    if negara == 'indonesia':
        lgt = 1.902 #id
    else:
        lgt = 2.8 #us

    wacc_persen = table_wacc[0]['WACC']
    fcf_t1 = (freecash['future3']['UFCF'] * (lgt/100)) + freecash['future3']['UFCF']
    terminal_values = fcf_t1 / ((wacc_persen/100) - (lgt/100))
    jumlah_future = 3
    pv_terminal_value = terminal_values / ((1+(wacc_persen/100))**jumlah_future)

    terminal_Value = {
    'lGT' : lgt,
    'wacc%' : wacc_persen,
    'fcf(t+1)' : fcf_t1,
    'terminal_values' : terminal_values,
    'pv_terminal_value' : pv_terminal_value
    
    }

    terminal_Value = pd.DataFrame.from_dict(terminal_Value,orient='index')

    enterprise_Value = sum_pv_ufcf + terminal_Value[0]['pv_terminal_value']
    totalDebt_a = table_wacc[0]['totaldebt']
    annualCashAndCashEquivalents = B_S_start['QuoteTimeSeriesStore']['timeSeries']['annualCashAndCashEquivalents'][-1]['reportedValue']['raw']
    try:
        net_debt = B_S_start['QuoteTimeSeriesStore']['timeSeries']['annualNetDebt'][-1]['reportedValue']['raw']
    except:
        net_debt = totalDebt_a - annualCashAndCashEquivalents
    equity_value = enterprise_Value - net_debt
    share_outstanding = table_wacc[0]['Diluted Shares Outstanding']
    equity_Value_PerShare = equity_value / share_outstanding

    #======= lereved =========
    intrinsic_Value = {
        'Enterprise_Value' : enterprise_Value,
        'net_debt' : net_debt,
        'equity_value' : equity_value,
        'share_outstanding' : share_outstanding,
        'equity_Value_PerShare' : equity_Value_PerShare
    }

    intrinsic_Value = pd.DataFrame.from_dict(intrinsic_Value, orient='index')

    pricess = table_wacc[0]['Share Price']
    selisih = (equity_Value_PerShare - pricess)/pricess

    if selisih >= 0.50:
        nilai_wajar_dcf = (pricess*0.22)+pricess
    else:
        nilai_wajar_dcf = equity_Value_PerShare

    def fcf_levered(input1, fcf_start, ticker_code):
        if input1 == 'lastyear':
            year = 0
            input2 = -1
        elif input1 == 'yearago':
            year = 1
            input2 = -2
        elif input1 ==  'years2ago':
            year = 2
            input2 = -3
        elif input1 ==  'years3ago':
            year = 3
            input2 = -4
        elif input1 ==  'years4ago':
            year = 4
            input2 = -5
        else:
            print('out of index')
        
        try:
            operating_CashFlow = fcf_start['QuoteTimeSeriesStore']['timeSeries']['annualOperatingCashFlow'][input2]['reportedValue']['raw']
        except:
            operating_CashFlow = 0
        operating_CashFlow_persen = operating_CashFlow / income_statement[input1]['revenue']
        Capital_Expenditure = freecash[input1]['Capital Expenditure']
        Capital_Expenditure_persen = Capital_Expenditure / income_statement[input1]['revenue']
        freecashflow = fcf_start['QuoteTimeSeriesStore']['timeSeries']['annualFreeCashFlow'][input2]['reportedValue']['raw']
        
        
        fcf_lereved = {}
        fcf_lereved[input1] = {}
        fcf_lereved[input1]['operating_CashFlow'] = operating_CashFlow
        fcf_lereved[input1]['operating_CashFlow(%)'] = operating_CashFlow_persen
        fcf_lereved[input1]['Capital_Expenditure'] = Capital_Expenditure
        fcf_lereved[input1]['Capital_Expenditure(%)'] = Capital_Expenditure_persen
        fcf_lereved[input1]['freecashflow'] = freecashflow
        
        return fcf_lereved

    fcf_lev_lastyear = fcf_levered('lastyear', fcf_start, ticker_code)
    fcf_lev_yearago = fcf_levered('yearago', fcf_start, ticker_code)
    fcf_lev_years2ago = fcf_levered('years2ago', fcf_start, ticker_code)

    fcf_levered = fcf_lev_years2ago | fcf_lev_yearago | fcf_lev_lastyear
    avg_operating_CashFlow_persen = (fcf_levered['years2ago']['operating_CashFlow(%)'] + fcf_levered['yearago']['operating_CashFlow(%)'] + fcf_levered['lastyear']['operating_CashFlow(%)'])/3
    operating_CashFlow_future1 = avg_operating_CashFlow_persen * freecash['future1']['revenue']
    operating_CashFlow_future2 = avg_operating_CashFlow_persen * freecash['future2']['revenue']
    operating_CashFlow_future3 = avg_operating_CashFlow_persen * freecash['future3']['revenue']

    avg_Capital_Expenditure_persen = (fcf_levered['years2ago']['Capital_Expenditure(%)'] + fcf_levered['yearago']['Capital_Expenditure(%)'] + fcf_levered['lastyear']['Capital_Expenditure(%)'])/3
    Capital_Expenditure_future1 = avg_Capital_Expenditure_persen * freecash['future1']['revenue']
    Capital_Expenditure_future2 = avg_Capital_Expenditure_persen * freecash['future2']['revenue']
    Capital_Expenditure_future3 = avg_Capital_Expenditure_persen * freecash['future3']['revenue']

    freecashflow1 = operating_CashFlow_future1 + Capital_Expenditure_future1
    freecashflow2 = operating_CashFlow_future2 + Capital_Expenditure_future2
    freecashflow3 = operating_CashFlow_future3 + Capital_Expenditure_future3

    wacc_persen_L = table_wacc[0]['WACC']
    pv_lereved_fcf1 = freecashflow1 / (1+(wacc_persen_L/100))
    pv_lereved_fcf2 = freecashflow2 / (1+(wacc_persen_L/100))**2
    pv_lereved_fcf3 = freecashflow3 / (1+(wacc_persen_L/100))**3

    fcf_levered_future = {
        'future1' : { 
            'operating_CashFlow' : operating_CashFlow_future1,
            'operating_CashFlow(%)' : avg_operating_CashFlow_persen,
            'Capital_Expenditure' : Capital_Expenditure_future1,
            'Capital_Expenditure(%)' : avg_Capital_Expenditure_persen,
            'freecashflow' : freecashflow1,
            'wacc%' : wacc_persen_L,
            'PV_LFCF' : pv_lereved_fcf1
                    },
        
        'future2' : { 
            'operating_CashFlow' : operating_CashFlow_future2,
            'operating_CashFlow(%)' : avg_operating_CashFlow_persen,
            'Capital_Expenditure' : Capital_Expenditure_future2,
            'Capital_Expenditure(%)' : avg_Capital_Expenditure_persen,
            'freecashflow' : freecashflow2,
            'wacc%' : wacc_persen_L,
            'PV_LFCF' : pv_lereved_fcf2
                    },
        
        'future3' : { 
            'operating_CashFlow' : operating_CashFlow_future3,
            'operating_CashFlow(%)' : avg_operating_CashFlow_persen,
            'Capital_Expenditure' : Capital_Expenditure_future3,
            'Capital_Expenditure(%)' : avg_Capital_Expenditure_persen,
            'freecashflow' : freecashflow3,
            'wacc%' : wacc_persen_L,
            'PV_LFCF' : pv_lereved_fcf3
                    },
    }

    fcf_levered = fcf_lev_years2ago | fcf_lev_yearago | fcf_lev_lastyear | fcf_levered_future
    fcf_levered = pd.DataFrame.from_dict(fcf_levered,orient='columns')

    sum_pv_lereved = pv_lereved_fcf1 + pv_lereved_fcf2 + pv_lereved_fcf3
    fcf_lereved_p1 = (fcf_levered['future3']['freecashflow'] * (lgt/100)) + fcf_levered['future3']['freecashflow']
    terminal_values_lereved = fcf_lereved_p1 / ((wacc_persen/100) - (lgt/100))
    pv_terminal_value = terminal_values_lereved / ((1+(wacc_persen/100))**jumlah_future)
    enterprise_value_lereved = sum_pv_lereved + pv_terminal_value
    equity_value_lereved = enterprise_value_lereved - net_debt
    equity_Value_PerShare_lereved = equity_value_lereved / share_outstanding
    nilai_wajar_lereved = equity_Value_PerShare_lereved

    return nilai_wajar_dcf, nilai_wajar_lereved


coba = dcf_and_lereved('SIDO', 'indonesia')[0]
coba2 = dcf_and_lereved('SIDO', 'indonesia')[1]
print('nilai wajar DCF = ', coba)
print('nilai wajar DCF_lereved = ', coba2)

