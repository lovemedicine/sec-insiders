# Insider Trading Stock Price Predictor

This is a collection of python scripts and functions for creating a database of insider trades and using it to train a machine learning model. It is still a work in progress.

## Instructions

1. Install packages:

```
pip install -r requirements.txt
```

2. Then load ~8300 SEC companies from JSON into the sqlite database (`data/sec-insiders.db`):

```
python scripts/load_sec_companies.py
```

*NOTE*: Execute scripts from inside the project's root directory, otherwise they will fail.

3. Then run the script to fetch SEC form 4 filings for a specified number of companies:

```
python scripts/load_sec_form4_filings.py --num 10 --start_id 1
```

It will take a long time to process the form 4s. Occasionally the script encounters an error after only some of the form 4s are processed for a particular company. You'll need to use your sqlite client to delete the transactions for that company and run the script again beginning with that company's id. See `scripts/load_sec_form4_filings.py` for a full list of arguments the script accepts.

4. Once you've loaded enough transactions for your purposes, you can generate the training data.

The training data script makes use of historical stock values, which can be obtained for free with the yfinance python module, but it also uses market capitalization data, which will be fetched from the FMP API. Yahoo Finance has a market cap value taken from the company's last quarterly report, but I found this value to be questionable. FMP's API has a free plan which allows you to make 250 requests/day which is the best available option I found, and this is what this script uses, though you'll see useful code for other options in `lib/stocks.py`. You'll need to sign up for an [FMP API key](https://site.financialmodelingprep.com/developer/docs) and then copy `config.yml.default` to `config.yml` and paste your API key there.

Then run the script to generate training data:

```
python scripts/generate_training_data.py
```

This creates a file called `data/training_data.csv`.

5. Train your model using Keras:

```
python scripts/train_model.py
```

That's all for now!

## Useful SQL queries

### list companies with filings
```
select companies.id, companies.name, companies.ticker, companies.sec_cik, count(*) from transactions left join companies on (companies.id = transactions.company_id) group by companies.id;
```

### list people with most companies
```
select p.id, p.name, count(distinct c.id) as num, group_concat(distinct c.name) as companies from transactions t left join people p on (t.person_id = p.id) left join companies c on (t.company_id = c.id) group by p.id having num > 1 order by num desc;
```
