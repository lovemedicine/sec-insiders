import csv
import argparse
from pprint import pprint

import sys
sys.path.append('./lib')
from db import create_session
from models import Transaction, Company
from stocks import fetch_stock_price, fetch_market_cap
from dates import modify_date_str_with_delta

def generate_input_data_for_company(session, company):
    start_date = "2023-08-01"
    end_date = "2023-11-01"

    windows = [90, 180, 360, 720, 1440] # measured in days
    transaction_start_date = modify_date_str_with_delta(start_date, days=-windows[-1])

    transactions = session.\
        query(Transaction).\
        filter(Transaction.company_id == company.id).\
        filter(Transaction.date >= transaction_start_date).\
        filter(Transaction.date < start_date).\
        filter(Transaction.shares > 0).\
        filter(Transaction.price > 0).\
        all()

    print(str(len(transactions)) + " " + company.ticker + " transactions found")

    if (len(transactions) < 5):
        return None

    start_price = fetch_stock_price(company.ticker, start_date)
    end_price = fetch_stock_price(company.ticker, end_date)
    performance = float(start_price / end_price)
    market_cap = fetch_market_cap(company.ticker)
    sp_start_price = fetch_stock_price('SPY', start_date)
    sp_end_price = fetch_stock_price('SPY', end_date)
    sp_performance = float(sp_start_price / sp_end_price)
    rel_performance = performance / sp_performance

    input_data = generate_input_data_from_transactions(
        transactions,
        start_date,
        end_date,
        windows=windows,
        market_cap=market_cap
    )
    input_data['rel_performance'] = rel_performance

    return input_data

def generate_input_data_from_transactions(transactions, start_date, end_date, windows, market_cap):
    results = {}

    for i in range(len(windows)):
        window_start = windows[i]
        window_start_date = modify_date_str_with_delta(start_date, days=-window_start)

        window_transactions = [
            t for t in transactions if str(t.date) >= window_start_date and str(t.date) < end_date
        ]
        window_key = str(window_start) + '_'

        for direction in ['sale', 'purchase']:
            share_value = 0
            insiders = set()
            direction_transactions = [
                t for t in window_transactions if t.direction == direction
            ]

            for transaction in direction_transactions:
                share_value += float(transaction.shares * transaction.price * 100 / market_cap)
                insiders.add(transaction.person_id)

            results[window_key + direction + '_share_value'] = share_value
            results[window_key + direction + '_insider_count'] = len(insiders)

    return results

# parser = argparse.ArgumentParser()
# parser.add_argument('-t', '--ticker', required=True)
# args = parser.parse_args()
csv_data = []

with create_session() as session:
    company_ids = [row[0] for row in session.query(Transaction.company_id).distinct().all()]
    companies = session.query(Company).filter(Company.id.in_(company_ids)).all()
    num = len(companies)
    count = 1

    for company in companies:
        print(f"({count}/{num}) Processing {company.name}...")
        count += 1

        try:
            input_data = generate_input_data_for_company(session, company)
            if input_data == None:
                continue
            csv_data.append(input_data)
        except Exception as err:
            print(f'Error: {str(err)}')

keys = csv_data[0].keys()

with open('./data/training_data.csv', 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(csv_data)

