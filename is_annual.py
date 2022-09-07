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