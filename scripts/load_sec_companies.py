import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import sys
sys.path.append('./lib')
from models import Base, Company
from db import create_session

def load_sec_companies_data():
    with open('../data/sec_companies.json') as json_file:
        json_data = json.load(json_file)
        return list(json_data.values())

def company_exists(session, data):
    sec_cik = format_cik(data['sec_cik'])
    return session.query(
        session.query(Company).filter(Company.sec_cik == sec_cik).exists()
    ).scalar()

def format_cik(cik):
    return f'{data["sec_cik"]:010}'

def save_company(session, data):
    company = Company(
        name=data['name'],
        ticker=data['ticker'],
        sec_cik = format_cik(data['sec_cik'])
    )
    session.add_all([company])

companies = load_sec_companies_data()

with create_session() as session:
    for data in companies:
        if not company_exists(session, data):
            save_company(session, data)

    session.commit()
