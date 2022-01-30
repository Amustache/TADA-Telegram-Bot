import os


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError


from secret import BASE_URL, SPREADSHEET_ID


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
VALUE_INPUT_OPTION = "RAW"
CATEGORIES_RANGE = "Data!A2:A7"
NEXT_ID = "Data!B2"
ROW_RANGE = "Data!C{}"


def get_spreadsheets_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def get_categories_from_sheet(service):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=CATEGORIES_RANGE).execute()
        categories = [cat[0] for cat in result.get("values", [])]
        return categories
    except HttpError as err:
        return [err]


def get_and_update_next_id(service):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=NEXT_ID).execute()
        next_id = int(result.get("values", [])[0][0])

        # Update id
        values = [[next_id + 1]]
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(spreadsheetId=SPREADSHEET_ID, range=NEXT_ID, valueInputOption=VALUE_INPUT_OPTION, body=body)
            .execute()
        )

        return next_id
    except HttpError as err:
        return [err]


def add_new_item(service, pic_id, user_id, pic_dict):
    try:
        values = [
            [
                pic_id,
                user_id,
                BASE_URL.format(pic_dict["filename"].split("/")[-1]),
                pic_dict["title"],
                pic_dict["link"],
                "{}".format("Yes, {}".format(pic_dict["nsfw"]) if pic_dict["nsfw"] else "No"),
                pic_dict["at"],
                pic_dict["author"],
            ]
        ]
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=SPREADSHEET_ID,
                range=ROW_RANGE.format(pic_id + 1),
                valueInputOption=VALUE_INPUT_OPTION,
                body=body,
            )
            .execute()
        )
    except HttpError as err:
        return [err]
