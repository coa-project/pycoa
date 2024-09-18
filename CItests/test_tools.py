#to run all tests.
#pytest tests/test_tools.py
#to run a specific test
#pytest tests/test_tools.py::test_tostdstring

import pytest
import sys
import os
import datetime as dt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coa.tools import (
    tostdstring, 
    fill_missing_dates, 
    check_valid_date, 
    extract_dates, 
    week_to_date, 
    exists_from_url, 
    get_local_from_url, 
    flat_list, 
    datetime,
    pd)
from coa.error import CoaKeyError, CoaTypeError, CoaConnectionError

# ------------------------- test tostdstring ------------------------------
def test_tostdstring():
    assert tostdstring("Test-string") == "TEST STRING", "Error with '-'"
    assert tostdstring("Café") == "CAFE", "Error with accented characters"
    assert tostdstring("test   string") == "TEST STRING", "Error with multiple spaces"
    assert tostdstring("éçà") == "ECA", "Error with multiple accented characters"

# ------------------------- test fill_missing_dates------------------------------
def test_fill_missing_dates():
    data = {
        'date': [datetime.date(2023, 6, 1), datetime.date(2023, 6, 3)],
        'where': ['A', 'A']
    }
    df = pd.DataFrame(data)
    filled_df = fill_missing_dates(df)
    assert len(filled_df) == 3
    assert datetime.date(2023, 6, 2) in filled_df['date'].values, "Error with fill missing date"

# ------------------------- test check_valid_date------------------------------
def test_check_valid_date():
    assert check_valid_date("01/01/2023") == datetime.date(2023, 1, 1)
    with pytest.raises(CoaTypeError):
        check_valid_date("2023/01/01")
    with pytest.raises(CoaTypeError):
        check_valid_date("32/01/2023")
    with pytest.raises(CoaTypeError):
        check_valid_date("01/13/2023")
    with pytest.raises(CoaTypeError):
        check_valid_date("01/01/23")
    with pytest.raises(CoaTypeError):
        check_valid_date("01-01-2023")

# ------------------------- test extract_date------------------------------
def test_extract_dates():
    assert extract_dates("01/01/2020:31/12/2020") == (datetime.date(2020, 1, 1), datetime.date(2020, 12, 31)), "Error with full date"
    assert extract_dates("") == (datetime.date(1, 1, 1), datetime.date.today()), "Error with empty string"

# ------------------------- test weektodate ------------------------------
def test_week_to_date():
    assert week_to_date("2023-01-01-2023-01-07") == datetime.date(2023, 1, 4), "Error with rolling week format"
    assert week_to_date("2023-01-01") == datetime.date(2023, 1, 4), "Error with single week format"

# ------------------------- test exist url------------------------------
def test_exists_from_url():
    assert exists_from_url("https://www.google.com"), "Error with existing URL"
    assert not exists_from_url("http://thisurldoesnotexist.com"), "Error with non-existing URL"

# ------------------------- test getlocalfromurl ------------------------------
def test_get_local_from_url():
    url = "https://www.google.com/robots.txt"
    local_filename = get_local_from_url(url)
    assert os.path.exists(local_filename), "Error downloading or storing file from URL"

# ------------------------- test flatlist ------------------------------
def test_flat_list():
    assert flat_list([[1, 2], [3, 4]]) == [1, 2, 3, 4], "Error with nested list"
    assert flat_list([1, [2, 3], 4]) == [1, 2, 3, 4], "Error with mixed list"

####this test is not working
# def test_return_nonan_dates_pandas():
#     data = {
#         'date': [datetime.date(2023, 6, 1), datetime.date(2023, 6, 2), datetime.date(2023, 6, 3)],
#         'value': [1, pd.NA, 3]
#     }
#     df = pd.DataFrame(data)
#     cleaned_df = return_nonan_dates_pandas(df, 'value')
#     assert len(cleaned_df) == 2, f"Expected 2 rows but got {len(cleaned_df)}"
#     assert datetime.date(2023, 6, 1) in cleaned_df['date'].values, "Missing valid date after cleaning"
#     assert datetime.date(2023, 6, 3) in cleaned_df['date'].values, "Missing valid date after cleaning"



