# 🌐 Identity Reconciliation: Identify Contact API

A Django REST Framework application to manage contact identities based on email and phone numbers. The system detects and merges contacts into a single primary identity while linking all secondary information (emails and phone numbers) to avoid duplication and ensure consistency.


## 🔧 Problem Statement

Build an API endpoint `/identify/` that, given an email and/or phone number, identifies a contact and maintains associations between entries with overlapping information. The logic must ensure:

- **Primary contact** is created when no existing match is found.
- **Secondary contacts** are created and linked if a match is found (via either email or phone number).
- If multiple existing contacts are matched, they are **merged** under the earliest primary contact (by creation time).

---

## 🧪 Example Behavior

1. `POST /identify/` with:
```json
{
    "email": "a@example.com",
    "phoneNumber": "8888"
}
```

2. `POST /identify/` with:
```json
{
    "email": "b@example.com",
    "phoneNumber": "8888"
}
```

## Features
- Link multiple emails and phones to a contact.
- Merge duplicate contacts on the fly.
- Return consistent response schema with:
  -primaryContactId
  -List of all emails, phoneNumbers
  -secondaryContactIds



# How to Run
1. Clone and Setup Environment
```bash
git clone https://github.com/your-repo/identify-contact.git
cd identify-contact
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

2. Run Migrations
```bash
python manage.py migrate
```

3. Run Server
```bash
python manage.py runserver
```

## Running Tests
```bash
python manage.py test contacts
```

## API Example
Request
```bash
POST /identify/
Content-Type: application/json

{
  "email": "alice@example.com",
  "phoneNumber": "1234567890"
}
```

Response
```bash
{
  "contact": {
    "primaryContactId": 1,
    "emails": ["alice@example.com", "bob@example.com"],
    "phoneNumbers": ["1234567890", "9876543210"],
    "secondaryContactIds": [2, 3]
  }
}
```

### Requirements
Python 3.8+
Django 4.x
Django REST Framework


  
  
    
   


