Very Important:

- Use OAuth with service account instead of username/password auth
  https://developers.google.com/identity/protocols/oauth2/service-account#python Just Works, something like:

```python
from apiclient import discovery
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file('service_acct_private_key.json').with_scopes(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

driveService = discovery.build('drive', 'v3', credentials=creds)

discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
sheetsService = discovery.build('sheets', 'v4', credentials=credentials, discoveryServiceUrl=discoveryUrl)
```

(but with the pickling reuse we currently use for auth)

Normal Importance:

- Better factor GDrive auth stuff into shared code
- `scripts` directory
- `requirements.txt`
- a better secrets story than manually pasting files onto the server

- a better polling story

Far off into the future:

- Backups to a secondary location
- Rewrite off of Python
