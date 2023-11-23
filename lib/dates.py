from datetime import datetime, timedelta

def modify_date_str_with_delta(date_str, **kwargs):
    # Convert the date string to a datetime object
    date = datetime.strptime(date_str, "%Y-%m-%d")

    # Add a single day to the date
    new_date = date + timedelta(**kwargs)

    # Convert the new date back to a string in the same format
    return new_date.strftime("%Y-%m-%d")

