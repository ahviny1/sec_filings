'''
Created on Jan 26, 2013

@author: akittredge
'''
import requests
from BeautifulSoup import BeautifulSoup
import datetime
from urlparse import urljoin
import blist
import xml.etree.ElementTree as ET
import time
import csv
from requests.exceptions import ConnectionError
from financial_fundamentals.sec_filing import Filing
import re


def get_filings(symbol, filing_type):
    '''Get the last xbrl filed before date.
        Returns a Filing object, return None if there are no XBRL documents
        prior to the date.

        Step 1 Search for the ticker and filing type,
        generate the urls for the document pages that have interactive data/XBRL.
       Step 2 : Get the document pages, on each page find the url for the XBRL document.
        Return a blist sorted by filing date.
    '''

    filings = blist.sortedlist(key=_filing_sort_key_func)
    document_page_urls = _get_document_page_urls(symbol, filing_type)
    for url in document_page_urls:
        filing = _get_filing_from_document_page(url)
        filings.add(filing)
    for i in range(len(filings) - 1):
        filings[i].next_filing = filings[i + 1]
    return filings

SEARCH_URL = ('http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&'
              'CIK={symbol}&type={filing_type}&dateb=&owner=exclude&count=100')
def _get_document_page_urls(symbol, filing_type):
    '''Get the edgar filing document pages for the CIK.
    
    '''
    search_url = SEARCH_URL.format(symbol=symbol, filing_type=filing_type)
    search_results_page = get_edgar_soup(url=search_url)
    xbrl_rows = [row for row in 
                 search_results_page.findAll('tr') if 
                 row.find(text=re.compile('Interactive Data'))]
    for xbrl_row in xbrl_rows:
        documents_page = xbrl_row.find('a', {'id' : 'documentsbutton'})['href']
        documents_url = 'http://sec.gov' + documents_page
        yield documents_url

def _get_filing_from_document_page(document_page_url):
    '''Find the XBRL link on a page like 
    http://www.sec.gov/Archives/edgar/data/320193/000119312513300670/0001193125-13-300670-index.htm
    http://www.sec.gov/Archives/edgar/data/1350653/000135065316000097/atec-20160630-index.htm
    '''
    filing_page = get_edgar_soup(url=document_page_url)
    period_of_report_elem = filing_page.find('div', text='Filing Date')
    filing_date = period_of_report_elem.findNext('div', {'class' : 'info'}).text
    filing_date = datetime.date(*map(int, filing_date.split('-')))
    type_tds = filing_page.findAll('td', text='EX-101.INS')
    for type_td in type_tds:
        try:
            xbrl_link = type_td.findPrevious('a', text=re.compile('\.xml$')).parent['href']
        except AttributeError:
            continue
        else:
            if not re.match(pattern='\d\.xml$', string=xbrl_link):
                # we don't want files of the form 'jcp-20120504_def.xml'
                continue
            else:
                break
    xbrl_url = urljoin('http://www.sec.gov', xbrl_link)
    filing = Filing.from_xbrl_url(filing_date=filing_date, xbrl_url=xbrl_url)
    return filing

def _filing_sort_key_func(filing_or_date):
    if isinstance(filing_or_date, Filing):
        return filing_or_date.date
    elif isinstance(filing_or_date, datetime.datetime):
        return filing_or_date.date()
    else:
        return filing_or_date
    
def get_edgar_soup(url):
    response = get(url)
    return BeautifulSoup(response)

def get(url):
    '''requests.get wrapped in a backoff retry.
    
    '''
    wait = 0
    while wait < 5:
        try:
            return requests.get(url).text
        except ConnectionError:
            print 'ConnectionError, trying again in ', wait
            time.sleep(wait)
            wait += 1
    else:
        raise

S_P_500_TICKERS = ['ATEC', 'A', 'AA', 'AAPL', 'ABBV', 'ABC', 'ABT', 'ACE', 'ACN', 
                   'ACT', 'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'ADT', 'AEE',
                    'AEP', 'AES', 'AET', 'AFL', 'AGN', 'AIG', 'AIV', 'AIZ',
                     'AKAM', 'ALL', 'ALTR', 'ALXN', 'AMAT', 'AMD', 'AMGN', 
                     'AMP', 'AMT', 'AMZN', 'AN', 'ANF', 'AON', 'APA', 'APC',
                      'APD', 'APH', 'APOL', 'ARG', 'ATI', 'AVB', 'AVP', 'AVY',
                       'AXP', 'AZO', 'BA', 'BAC', 'BAX', 'BBBY', 'BBT', 'BBY',
                        'BCR', 'BDX', 'BEAM', 'BEN', 'BF.B', 'BHI', 'BIIB', 
                        'BK', 'BLK', 'BLL', 'BMC', 'BMS', 'BMY', 'BRCM', 
                        'BRK.B', 'BSX', 'BTU', 'BWA', 'BXP', 'C', 'CA', 
                        'CAG', 'CAH', 'CAM', 'CAT', 'CB', 'CBG', 'CBS', 'CCE',
                        'CCI', 'CCL', 'CELG', 'CERN', 'CF', 'CFN', 'CHK', 
                        'CHRW', 'CI', 'CINF', 'CL', 'CLF', 'CLX', 'CMA', 
                        'CMCSA', 'CME', 'CMG', 'CMI', 'CMS', 'CNP', 'CNX',
                         'COF', 'COG', 'COH', 'COL', 'COP', 'COST', 'COV', 
                         'CPB', 'CRM', 'CSC', 'CSCO', 'CSX', 'CTAS', 'CTL',
                         'CTSH', 'CTXS', 'CVC', 'CVH', 'CVS', 'CVX', 'D', 'DD',
                         'DE', 'DELL', 'DF', 'DFS', 'DG', 'DGX', 'DHI', 'DHR',
                          'DIS', 'DISCA', 'DLPH', 'DLTR', 'DNB', 'DNR', 'DO',
                        'DOV', 'DOW', 'DPS', 'DRI', 'DTE', 'DTV', 'DUK', 'DVA',
                        'DVN', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EIX', 'EL',
                        'EMC', 'EMN', 'EMR', 'EOG', 'EQR', 'EQT', 'ESRX', 
                        'ESV', 'ETFC', 'ETN', 'ETR', 'EW', 'EXC', 'EXPD',
                        'EXPE', 'F', 'FAST', 'FCX', 'FDO', 'FDX', 'FE', 
                        'FFIV', 'FHN', 'FIS', 'FISV', 'FITB', 'FLIR', 'FLR',
                        'FLS', 'FMC', 'FOSL', 'FRX', 'FSLR', 'FTI', 'FTR',
                        'GAS', 'GCI', 'GD', 'GE', 'GILD', 'GIS', 'GLW',
                        'GME', 'GNW', 'GOOG', 'GPC', 'GPS', 'GRMN', 'GS', 'GT',
                        'GWW', 'HAL', 'HAR', 'HAS', 'HBAN', 'HCBK', 'HCN', 
                        'HCP', 'HD', 'HES', 'HIG', 'HNZ', 'HOG', 'HON', 'HOT', 
                        'HP', 'HPQ', 'HRB', 'HRL', 'HRS', 'HSP', 'HST', 'HSY', 
                        'HUM', 'IBM', 'ICE', 'IFF', 'IGT', 'INTC', 'INTU', 'IP', 
                        'IPG', 'IR', 'IRM', 'ISRG', 'ITW', 'IVZ', 'JBL', 'JCI', 
                        'JCP', 'JDSU', 'JEC', 'JNJ', 'JNPR', 'JOY', 'JPM', 'JWN', 
                        'K', 'KEY', 'KIM', 'KLAC', 'KMB', 'KMI', 'KMX', 'KO', 
                        'KR', 'KRFT', 'KSS', 'L', 'LEG', 'LEN', 'LH', 'LIFE', 
                        'LLL', 'LLTC', 'LLY', 'LM', 'LMT', 'LNC', 'LO', 'LOW', 
                        'LRCX', 'LSI', 'LTD', 'LUK', 'LUV', 'LYB', 'M', 'MA', 
                        'MAR', 'MAS', 'MAT', 'MCD', 'MCHP', 'MCK', 'MCO', 
                        'MDLZ', 'MDT', 'MET', 'MHFI', 'MJN', 'MKC', 'MMC', 'MMM', 
                        'MNST', 'MO', 'MOLX', 'MON', 'MOS', 'MPC', 'MRK', 'MRO', 
                        'MS', 'MSFT', 'MSI', 'MTB', 'MU', 'MUR', 'MWV', 'MYL', 
                        'NBL', 'NBR', 'NDAQ', 'NE', 'NEE', 'NEM', 'NFLX', 'NFX', 
                        'NI', 'NKE', 'NOC', 'NOV', 'NRG', 'NSC', 'NTAP', 'NTRS', 
                        'NU', 'NUE', 'NVDA', 'NWL', 'NWSA', 'NYX', 'OI', 'OKE', 
                        'OMC', 'ORCL', 'ORLY', 'OXY', 'PAYX', 'PBCT', 'PBI', 
                        'PCAR', 'PCG', 'PCL', 'PCLN', 'PCP', 'PCS', 'PDCO', 
                        'PEG', 'PEP', 'PETM', 'PFE', 'PFG', 'PG', 'PGR', 'PH', 
                        'PHM', 'PKI', 'PLD', 'PLL', 'PM', 'PNC', 'PNR', 'PNW', 
                        'POM', 'PPG', 'PPL', 'PRGO', 'PRU', 'PSA', 'PSX', 'PVH', 
                        'PWR', 'PX', 'PXD', 'QCOM', 'QEP', 'R', 'RAI', 'RDC', 
                        'RF', 'RHI', 'RHT', 'RL', 'ROK', 'ROP', 'ROST', 'RRC', 
                        'RSG', 'RTN', 'S', 'SAI', 'SBUX', 'SCG', 'SCHW', 'SE', 
                        'SEE', 'SHW', 'SIAL', 'SJM', 'SLB', 'SLM', 'SNA', 'SNDK', 
                        'SNI', 'SO', 'SPG', 'SPLS', 'SRCL', 'SRE', 'STI', 'STJ', 
                        'STT', 'STX', 'STZ', 'SWK', 'SWN', 'SWY', 'SYK', 'SYMC', 
                        'SYY', 'T', 'TAP', 'TDC', 'TE', 'TEG', 'TEL', 'TER', 'TGT', 
                        'THC', 'TIF', 'TJX', 'TMK', 'TMO', 'TRIP', 'TROW', 'TRV', 
                        'TSN', 'TSO', 'TSS', 'TWC', 'TWX', 'TXN', 'TXT', 'TYC', 
                        'UNH', 'UNM', 'UNP', 'UPS', 'URBN', 'USB', 'UTX', 'V', 
                        'VAR', 'VFC', 'VIAB', 'VLO', 'VMC', 'VNO', 'VRSN', 'VTR', 
                        'VZ', 'WAG', 'WAT', 'WDC', 'WEC', 'WFC', 'WFM', 'WHR', 'WIN', 
                        'WLP', 'WM', 'WMB', 'WMT', 'WPO', 'WPX', 'WU', 'WY', 'WYN', 
                        'WYNN', 'X', 'XEL', 'XL', 'XLNX', 'XOM', 'XRAY', 'XRX', 'XYL', 
                        'YHOO', 'YUM', 'ZION', 'ZMH']



def append_to_csv(data):
    filename = 'results.csv'
    with open(filename, 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)
    return True

def find_violations(symbols, file_type):
    violated_urls = []
    for symbol in symbols:
        print 'Now searching ' + symbol + ' ...'
        counter = 0
        for url in _get_document_page_urls(symbol, file_type):
            file = _get_filing_from_document_page(url)
            xml_url = file._document._xbrl_url
            date = file.date
            data = get(xml_url).lower()
            bad_words = ['Until the Company achieves sustained profitability', 'does not have sufficient capital to meet its needs', 'continues to seek loans or equity placements to cover such cash needs', 'there can be no assurance that any additional funds will be available to cover expenses as they may be incurred', 'unable to raise additional capital', 'may be required to take additional measures to conserve liquidity', 'Suspending the pursuit of its business plan', 'The Company may need additional financing', 'We will incur expenses in connection with our SEC filing requirements and we may not be able to meet such costs', 'could jeopardize our filing status with the SEC', "raise substantial doubt about the Company's ability to continue as a going concern", 'taking certain steps to provide the necessary capital to continue its operations', "Executed an exchange agreement", "these factors raise substantial doubt about our ability to continue as a going concern", "If we do not obtain required additional equity or debt funding, our cash resources will be depleted and we could be required to materially reduce or suspend operations", "raise substantial doubt about our ability to continue as a going concern", "Our management intends to attempt to secure additional required funding through", "If we do not have sufficient funds to continue operations", "determined that it was out of compliance with certain of its financial covenants", "was in default of its covenants", "out of compliance with its financial convenants", "out of compliance with the company's financial convenants", "Has incurred consistent losses", "Has limited liquid assets", "dependent upon outside financing to continue operations", "plans to raise funds via private placements of its common stock and/or the issuance of debt instruments", "There is no assurance that the Company will be able to obtain the necessary funds through continuing equity and debt financing", "suspend the declaration of any further distributions on its", "to defer its interest payment"]
            #print bad_words
            if any(badWord.lower() in data for badWord in bad_words):
                data = [date, symbol, url]
                if append_to_csv(data):
                    print 'results.csv Successfully updated.'
                counter += 1
                violated_urls.append(url)
        print 'Found ' + str(counter) + ' filing violtions in ' + symbol
    print 'All violated SEC filings stated below please copy and paste ...'
    print violated_urls

def get_symbols_via_csv(filename):
    symbols = []
    with open(filename, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, dialect=csv.excel_tab)
        for row in reader:
            symbols.append(row['Symbol'])
    return symbols
    #print symbols

#get_symbols_via_csv('companylist.csv')

find_violations(get_symbols_via_csv('test.csv'), '10-Q')

