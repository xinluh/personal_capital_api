# Personal Capital (Empower) API

A minimalistic wrapper to Personal Capital / Empower Dashboard API.

## Requirements

- Python 3.6+
- Only dependency is `requests`

## Installation
```
python -m pip install git+https://github.com/xinluh/personal_capital_api.git@main
```
Or add to `requirements.txt` or `pyproject.toml` etc. depending on your package manager.

## Usage

### Log in
```python
from personal_capital_api import PersonalCapital

# will prompt for 2-factor login code that will be sent to text
pc = PersonalCapital().login(email, password, auth_method='sms')
```
You should run this at least once interactively so you can enter the 2-factor code manually.

After the first successful login, the cookies will be cached in `~/.cache/personal_capital_api` (or `C:\Users\Username\AppData\Local\PersonalCapitalApi\Cache` on Windows) and reloaded automatically next time, so likely you will only deal with 2-factor prompt only once. If you don't want this behavior, initiate the class with `PersonalCapital(use_cookies_cache=False)`.

### Get account information
```python
pc.get_accounts()
```

Example data returned:
```
{
    "creditCardAccountsTotal": 1000.00,
    "assets": 0,
    "otherLiabilitiesAccountsTotal": 0,
    "cashAccountsTotal": 0,
    "liabilities": 1000.00,
    "networth": -1000.00,
    "investmentAccountsTotal": 0,
    "mortgageAccountsTotal": 0,
    "loanAccountsTotal": 0,
    "otherAssetAccountsTotal": 0,
    "accounts": [
        {
            "name": "Some Credit Card",
            "firmName": "Some Company",
            "aggregating": false,
            "balance": 1000.00,
            "lastRefreshed": 1700881375000,
            "userAccountId": 1111111,
            "accountTypeGroup": "CREDIT_CARD",
            "oldestTransactionDate": "2023-01-01",
            "createdDate": 1700881327000,
            "closedDate": "",
            ...
        }
    ]
}
```

### Get transactions
```python
pc.get_transactions(start_date='2023-11-01', end_date='2023-11-30')
```

Example data returned:

```
 {
    "userTransactionId": 123456,
    "transactionDate": "2023-11-13",
    "isDuplicate": false,
    "status": "posted"
    "description": "Family Mart",
    "originalDescription": "Familymart",
    "simpleDescription": "Family Mart",
    "merchant": "Family Mart",
    "amount": 1.00,
    "originalAmount": 1.00,
    "accountName": "Some Credit Card",
    "userAccountId": 1111111,
    "categoryName": "Groceries",
    "categoryId": 17,
    "isCredit": false,
    "isEditable": true,
    "isCashOut": true,
    "merchantId": "_fpch1h4qecJohBZL-NUW5WMR-he1_yyUee1VnlBWBQ",
    "price": 0,
    "currency": "USD",
    "merchantType": "OTHERS",
    "isSpending": true,
    "isInterest": false,
    "transactionTypeId": 175,
    "isIncome": false,
    "includeInCashManager": true,
    "isNew": false,
    "isCashIn": false,
    "transactionType": "Purchase",
    "categoryType": "EXPENSE",
    "isCost": false,
    "subType": "PURCHASE",
    "hasViewed": false,
}
```
