import argparse
import time
import requests
from sqlalchemy import select
from datetime import datetime
from bs4 import BeautifulSoup
from nameparser import HumanName

import sys
sys.path.append('./lib')
from db import create_session
from models import Person, Company, Transaction

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-n', '--num', default=1)
parser.add_argument('-o', '--offset', default=None)
parser.add_argument('-t', '--ticker', default=None)
parser.add_argument('-i', '--start_id', default=None)

# parser.add_argument('-s', '--skip', action='store_true')
args = parser.parse_args()

def verbose_print(str):
    if args.verbose:
        print(str)

def fetch_sec_company_filings_data(company):
    # sleep to ensure no more than 10 requests per second
    # see https://www.sec.gov/developer
    time.sleep(0.1)
    url = f'https://data.sec.gov/submissions/CIK{company.sec_cik}.json'
    response = requests.get(url, headers=headers)
    return response.json()

def prepare_sec_company_filing_url(filing, readable=False):
    cik = filing['company_cik']
    accession = filing['accession_no'].replace('-', '')
    if filing['primary_doc']:
        file = filing['primary_doc'] if readable else filing['primary_doc'].split('/')[-1]
    else:
        file = 'doc4.xml'

    return f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{file}'

def fetch_sec_form4(filing):
    # sleep to ensure no more than 10 requests per second
    # see https://www.sec.gov/developer
    time.sleep(0.05)
    url = prepare_sec_company_filing_url(filing)
    verbose_print("Fetching form 4: " + url)
    verbose_print("Readable version: " + prepare_sec_company_filing_url(filing, readable=True))
    response = requests.get(url, headers=headers)
    return response.text

def parse_form4_xml(session, xml):
    soup = BeautifulSoup(xml, features="xml")
    person_data = parse_form4_person(soup)
    transactions = parse_form4_transactions(soup)
    # skip for now:
    # first_name, last_name = parse_person_name(person_data['name'])

    saved_person = session.query(Person).filter(Person.sec_cik == person_data['sec_cik']).first()

    person = saved_person or Person(
        name=person_data['name'],
        sec_cik=person_data['sec_cik']
    )

    for transaction in transactions:
        transaction.is_director = person_data['is_director']
        transaction.is_executive = person_data['is_executive']
        transaction.is_owner = person_data['is_owner']
        transaction.person_title = person_data['person_title']

    return person, transactions

# unused for now
def parse_person_name(name):
    hn = HumanName(name.replace(' ', ', ', 1))
    return hn.first, hn.last

def person_exists(session, data):
    sec_cik = format_cik(data['sec_cik'])
    return session.query(
        session.query(Person).filter(Person.sec_cik == sec_cik).exists()
    ).scalar()

def parse_bool(soup, tagName):
    tag = soup.find(tagName)
    value = tag and tag.string

    if value == None:
        return False

    if value.lower() == 'true':
        return True

    if value.lower() == 'false':
        return False

    return bool(int(value))

def parse_form4_person(soup):
    return dict(
        name=soup.rptOwnerName.string,
        sec_cik=soup.rptOwnerCik.string,
        is_director=parse_bool(soup, 'isDirector'),
        is_executive=parse_bool(soup, 'isOfficer'),
        is_owner=parse_bool(soup, 'isTenPercentOwner'),
        person_title=soup.officerTitle.string if soup.officerTitle else None
    )

def is_purchase_or_sale(transaction_elem):
    return transaction_elem.transactionCode.string in ['P', 'S']

def to_date_obj(date):
    return datetime.strptime(date, '%Y-%m-%d').date()

def parse_form4_transactions(soup):
    # only keep purchases or sales (not interested in exercising of options, etc)
    stock_data = list(filter(is_purchase_or_sale, soup.find_all(['nonDerivativeTransaction'])))
    option_data = list(filter(is_purchase_or_sale, soup.find_all(['derivativeTransaction'])))
    transactions = []

    for stock in stock_data:
        try:
            transaction = Transaction(
                security_type='stock',
                date=to_date_obj(stock.transactionDate.value.string),
                direction=('purchase' if stock.transactionCode.string == 'P' else 'sale'),
                shares=int(float(stock.transactionShares.value.string)),
                price=float(stock.transactionPricePerShare.value.string),
                is_direct=stock.directOrIndirectOwnership.value.string == 'D'
            )
            transactions.append(transaction)
        except BaseException as error:
            print("An error occured!")
            print(str(error))

    return transactions

def transform_data_into_filings(data):
    recent = data['filings']['recent']
    num = len(recent['form'])

    filings = []

    for i in range(num):
        filings.append({
            'company_cik': data['cik'],
            'form': recent['form'][i],
            'filing_date': recent['filingDate'][i],
            'accession_no': recent['accessionNumber'][i],
            'primary_doc': recent['primaryDocument'][i]
        })

    filings
    return filings

def already_processed_transaction(session, accession_no):
    return session.query(
        session.query(Transaction).filter(Transaction.accession_no == accession_no).exists()
    ).scalar()

def already_processed_company(session, company_id):
    return session.query(
      session.query(Transaction).filter(Transaction.company_id == company_id).exists()
    ).scalar()

headers = {
    "User-Agent": "Skomputer LLC matthew.skomarovsky@gmail.com"
}

with create_session(echo=args.verbose) as session:
    query = session.query(Company)

    if args.ticker != None:
        query = query.filter(Company.ticker == args.ticker)
    elif args.start_id != None:
        query = query.filter(Company.id >= args.start_id)
    else:
        if args.offset != None:
            query = query.offset(int(args.offset))

    companies = query.all()

    processed = 0
    num = int(args.num)

    for company in companies:
        if processed >= num:
            break

        if already_processed_company(session, company.id):
            print("*** Already processed " + company.name + "; skipping...")
            continue

        processed += 1

        data = fetch_sec_company_filings_data(company)
        filings = transform_data_into_filings(data)
        print("*** Company: " + company.name)
        print("*** Filings: " + str(len(filings)))
        count = 0

        for filing in filings:
            count += 1
            print("*** Processing filing " + str(count))

            if filing['form'] != '4':
                verbose_print("*** Skipping form " + filing['form'])
                continue

            if filing['primary_doc'][-3:] != 'xml':
                verbose_print("*** Skipping document " + filing['primary_doc'])
                continue

            accession_no = filing['accession_no']
            filing_date = filing['filing_date']

            if already_processed_transaction(session, accession_no):
                continue

            xml = fetch_sec_form4(filing)

            try:
                person, transactions = parse_form4_xml(session, xml)
            except BaseException as error:
                print("XML filing: ", prepare_sec_company_filing_url(filing))
                print("Readable filing: ", prepare_sec_company_filing_url(filing, readable=True))
                raise

            if len(transactions) == 0:
                continue

            verbose_print("*** Adding person:" + person.name)
            verbose_print("*** Adding " + str(len(transactions)) + " transactions")

            session.add(person)

            for transaction in transactions:
                transaction.accession_no = accession_no
                transaction.filing_date = to_date_obj(filing_date)
                transaction.person = person
                transaction.company = company

            session.add_all(transactions)

            if not args.debug:
                session.commit()

        if args.debug:
            session.rollback()
