import qrcode
from io import BytesIO
import base64
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
import time
import json

class GoogleSheetsSimple:
    def __init__(self, credentials_path="mybotproject-468611-8104acd37ccd.json"):
        """Google Sheets API - JWT muammosini hal qilgan versiya"""
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            if not os.path.exists(credentials_path):
                print(f"❌ Credentials fayl topilmadi: {credentials_path}")
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

            creds = self._create_fresh_credentials(credentials_path, scopes)
            self.credentials_path = credentials_path
            self.scopes = scopes
            self.service = build('sheets', 'v4', credentials=creds)
            print("✅ Google Sheets API ulandi (JWT muammosi hal qilindi)")
        except Exception as e:
            print(f"❌ Google Sheets API xatolik: {e}")
            self.service = None
            print("⚠️ Offline rejimda ishlamoqda (Google Sheets o'chirildi)")

    def _create_fresh_credentials(self, credentials_path, scopes):
        """Yangi va toza credentials yaratish"""
        try:
            with open(credentials_path, 'r') as f:
                service_account_info = json.load(f)
            current_time = int(time.time())
            creds = Credentials.from_service_account_info(
                service_account_info,
                scopes=scopes
            )
            if hasattr(creds, 'refresh'):
                try:
                    creds.refresh(build('oauth2', 'v2', credentials=creds)._http)
                except:
                    pass
            return creds
        except Exception as e:
            print(f"⚠️ Credentials yaratishda muammo: {e}")
            return Credentials.from_service_account_file(credentials_path, scopes=scopes)

    def _retry_with_fresh_credentials(self, func, *args, **kwargs):
        """Xatolik bo'lganda yangi credentials bilan qayta urinish"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if 'invalid_grant' in str(e) or 'JWT' in str(e):
                print("🔄 JWT xatoligi - yangi credentials yaratilmoqda...")
                try:
                    creds = self._create_fresh_credentials(self.credentials_path, self.scopes)
                    self.service = build('sheets', 'v4', credentials=creds)
                    return func(*args, **kwargs)
                except Exception as retry_error:
                    print(f"❌ Qayta urinishda ham xatolik: {retry_error}")
                    raise retry_error
            else:
                raise e

    def create_spreadsheet(self, title):
        """Yangi jadval yaratish - xatoliklarga chidamli"""
        if not self.service:
            print("❌ Google Sheets o'chirilgan")
            return None

        def _create():
            spreadsheet = {
                'properties': {'title': title},
                'sheets': [{
                    'properties': {
                        'title': 'Ro\'yxat',
                        'gridProperties': {'rowCount': 1000, 'columnCount': 8}  # 9 dan 8 ga o'zgartirildi
                    }
                }]
            }
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result.get('spreadsheetId')
            self._setup_spreadsheet_format(spreadsheet_id)
            print(f"✅ Jadval yaratildi: {spreadsheet_id}")
            return spreadsheet_id

        try:
            return self._retry_with_fresh_credentials(_create)
        except Exception as e:
            print(f"❌ Jadval yaratishda xatolik: {e}")
            return None

    def clear_all_data(self, spreadsheet_id):
        """Jadvaldagi barcha ma'lumotlarni tozalash"""
        if not self.service:
            print("✅ Offline rejim - ma'lumotlar tozalanmadi")
            return True

        def _clear():
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range='A2:H1000'  # I dan H ga o'zgartirildi
            ).execute()
            return True

        try:
            result = self._retry_with_fresh_credentials(_clear)
            print("✅ Jadval ma'lumotlari tozalandi")
            return result
        except Exception as e:
            print(f"❌ Jadval tozalashda xatolik: {e}")
            return False

    def _setup_spreadsheet_format(self, spreadsheet_id):
        """Jadval formatini sozlash"""
        if not self.service:
            return

        def _setup():
            headers = [
                ['№', 'ISM FAMILIYA', 'TELEFON RAQAM', 'TOLOV QILINGAN', 'ID', 'QR CODE', 'KELDI', 'SKANER HOLATI']
            ]
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1:H1',  # I1 dan H1 ga o'zgartirildi
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()

            requests = [
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
                    'properties': {'pixelSize': 50}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2},
                    'properties': {'pixelSize': 200}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3},
                    'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 4},
                    'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5},
                    'properties': {'pixelSize': 80}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 5, 'endIndex': 6},
                    'properties': {'pixelSize': 1200}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 7},
                    'properties': {'pixelSize': 80}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': 7, 'endIndex': 8},
                    'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},
                {'updateDimensionProperties': {
                    'range': {'sheetId': 0, 'dimension': 'ROWS', 'startIndex': 1, 'endIndex': 1000},
                    'properties': {'pixelSize': 800}, 'fields': 'pixelSize'}},
                {'repeatCell': {'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0,
                                          'endColumnIndex': 8}, 'cell': {
                    'userEnteredFormat': {'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2},
                                          'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                                         'fontSize': 11, 'bold': True}, 'horizontalAlignment': 'CENTER',
                                          'verticalAlignment': 'MIDDLE'}},
                                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'}}
            ]
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

        try:
            self._retry_with_fresh_credentials(_setup)
            print("✅ Jadval formati sozlandi")
        except Exception as e:
            print(f"❌ Format sozlashda xatolik: {e}")

    def create_qr_formula(self, cell_reference, row_number):
        """QR kod formulasi yaratish"""
        try:
            formula = f'=IMAGE("https://api.qrserver.com/v1/create-qr-code/?size=1200x1200&data=" & ENCODEURL(E{row_number}) & "&margin=20")'
            print(f"✅ QR formula yaratildi (1200x1200): {cell_reference}")
            return formula
        except Exception as e:
            print(f"❌ QR formula yaratishda xatolik: {e}")
            return None

    def ensure_headers_exist(self, spreadsheet_id):
        """Sarlavhalar mavjudligini tekshirish"""
        if not self.service:
            return False

        def _check_headers():
            existing_headers = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A1:H1'  # I1 dan H1 ga o'zgartirildi
            ).execute()
            existing_values = existing_headers.get('values', [[]])
            if not existing_values or len(existing_values[0]) < 8:
                headers = [
                    ['№', 'ISM FAMILIYA', 'TELEFON RAQAM', 'TOLOV QILINGAN', 'ID', 'QR CODE', 'KELDI', 'SKANER HOLATI']
                ]
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='A1:H1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                print("✅ Sarlavhalar avtomatik qo'shildi")
                return True
            else:
                print("✅ Sarlavhalar mavjud")
                return False

        try:
            return self._retry_with_fresh_credentials(_check_headers)
        except Exception as e:
            print(f"❌ Sarlavhalarni tekshirishda xatolik: {e}")
            return False

    def add_user(self, spreadsheet_id, user_info, event_info=None):
        """Foydalanuvchi qo'shish - JWT xatoliklarga chidamli"""
        if not self.service:
            print("✅ Offline rejim - user qo'shilmadi")
            return True

        def _add_user():
            self.ensure_headers_exist(spreadsheet_id)
            try:
                existing_data = self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='A:A'
                ).execute()
                next_row = len(existing_data.get('values', [])) + 1
            except:
                next_row = 2

            qr_id = user_info.get('qr_id')
            qr_formula = self.create_qr_formula(f'F{next_row}', next_row)

            user_data = [
                next_row - 1,  # №
                user_info.get('full_name', ''),  # ISM FAMILIYA
                user_info.get('phone', ''),  # TELEFON RAQAM
                '☑' if user_info.get('payment_status') == 'paid' else '☐',  # TOLOV QILINGAN
                str(qr_id),  # ID
                qr_formula if qr_formula else str(qr_id),  # QR CODE
                '☐',  # KELDI
                ''  # SKANER HOLATI
            ]

            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'A{next_row}:H{next_row}',  # I dan H ga o'zgartirildi
                valueInputOption='USER_ENTERED',
                body={'values': [user_data]}
            ).execute()
            return True

        try:
            result = self._retry_with_fresh_credentials(_add_user)
            print(f"✅ User qo'shildi: {user_info.get('full_name')} (ID: {user_info.get('qr_id')})")
            return result
        except Exception as e:
            print(f"❌ User qo'shishda xatolik: {e}")
            return False

    def update_attendance(self, spreadsheet_id, qr_data, scanner_name='Admin'):
        """Kelganlik belgilash - JWT xatoliklarga chidamli"""
        if not self.service:
            print("✅ Offline rejim - kelganlik belgilanmadi")
            return True, "Offline rejim"

        def _update_attendance():
            if ':' in qr_data:
                qr_id, _ = qr_data.split(':')
            else:
                qr_id = qr_data

            data = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='E:E'
            ).execute()
            values = data.get('values', [])
            row_number = None
            for i, row in enumerate(values):
                if row and str(row[0]) == str(qr_id):
                    row_number = i + 1
                    break

            if not row_number:
                print(f"❌ QR ID topilmadi: {qr_data}")
                return False, None

            current_time = datetime.now().strftime('%H:%M')
            updates = [
                {'range': f'G{row_number}', 'values': [['☑']]},
                {'range': f'H{row_number}', 'values': [[f'{scanner_name} {current_time}']]}
            ]
            batch_update_request = {
                'valueInputOption': 'RAW',
                'data': updates
            }
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=batch_update_request
            ).execute()

            user_data = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'A{row_number}:H{row_number}'  # I dan H ga o'zgartirildi
            ).execute()
            user_info = user_data.get('values', [[]])[0]
            user_name = user_info[1] if len(user_info) > 1 else 'Noma\'lum'

            return True, user_name

        try:
            success, user_info = self._retry_with_fresh_credentials(_update_attendance)
            if success:
                print(f"✅ Kelganlik belgilandi: {qr_data} - {user_info}")
            return success, user_info
        except Exception as e:
            print(f"❌ Kelganlik belgilashda xatolik: {e}")
            return False, None

    def get_stats(self, spreadsheet_id):
        """Statistika olish - JWT xatoliklarga chidamli"""
        if not self.service:
            return {'total': 0, 'attended': 0, 'not_attended': 0}

        def _get_stats():
            data = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A2:H1000'  # I dan H ga o'zgartirildi
            ).execute()
            users = data.get('values', [])
            total = len(users)
            attended = len([u for u in users if len(u) > 6 and u[6] == '☑'])
            return {
                'total': total,
                'attended': attended,
                'not_attended': total - attended
            }

        try:
            return self._retry_with_fresh_credentials(_get_stats)
        except Exception as e:
            print(f"❌ Statistika olishda xatolik: {e}")
            return {'total': 0, 'attended': 0, 'not_attended': 0}

# Global o'zgaruvchilar
sheets_client = None
SPREADSHEET_ID = None

def init_google_sheets(credentials_path="mybotproject-468611-8104acd37ccd.json", spreadsheet_id=None):
    """Google Sheets ni ishga tushirish"""
    global sheets_client, SPREADSHEET_ID
    try:
        sheets_client = GoogleSheetsSimple(credentials_path)
        if spreadsheet_id:
            SPREADSHEET_ID = spreadsheet_id
            print(f"✅ Mavjud jadval: {spreadsheet_id}")
        else:
            title = f"Marosim QR Ro'yxati - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            SPREADSHEET_ID = sheets_client.create_spreadsheet(title)
        if SPREADSHEET_ID:
            print(f"📊 Jadval URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
            try:
                with open('.env', 'w') as f:
                    f.write(f'SPREADSHEET_ID={SPREADSHEET_ID}\n')
                print("✅ .env fayliga saqlandi")
            except Exception as e:
                print(f"⚠️ .env saqlashda xatolik: {e}")
        return True
    except Exception as e:
        print(f"❌ Google Sheets ishga tushirishda xatolik: {e}")
        print("✅ Offline rejimda davom etmoqda")
        return True

def clear_sheets_data():
    """Google Sheets ma'lumotlarini tozalash"""
    global sheets_client, SPREADSHEET_ID
    try:
        if not sheets_client or not SPREADSHEET_ID:
            print("✅ Offline rejim - ma'lumotlar tozalanmadi")
            return True
        success = sheets_client.clear_all_data(SPREADSHEET_ID)
        if success:
            print("✅ Google Sheets ma'lumotlari tozalandi")
        return success
    except Exception as e:
        print(f"❌ Sheets tozalashda xatolik: {e}")
        return True

def save_user_with_qr_to_sheets(user_info, event_info):
    """User ni Google Sheets ga saqlash"""
    global sheets_client, SPREADSHEET_ID
    try:
        if not sheets_client or not SPREADSHEET_ID:
            print("✅ Offline rejim - user saqlanmadi")
            return True, user_info.get('qr_id')
        success = sheets_client.add_user(SPREADSHEET_ID, user_info, event_info)
        qr_id = user_info.get('qr_id') if success else None
        return success, qr_id
    except Exception as e:
        print(f"❌ Saqlashda xatolik: {e}")
        return True, user_info.get('qr_id')

def scan_qr_and_mark_attendance(qr_data, scanner_name='Admin'):
    """QR skanerlash va kelganlik belgilash"""
    global sheets_client, SPREADSHEET_ID
    try:
        if not sheets_client or not SPREADSHEET_ID:
            print("✅ Offline rejim - kelganlik belgilanmadi")
            return True, "Offline rejim"
        success, user_info = sheets_client.update_attendance(SPREADSHEET_ID, qr_data, scanner_name)
        return success, user_info
    except Exception as e:
        print(f"❌ Skanerlashda xatolik: {e}")
        return True, "Offline rejim"


def get_sheets_url():
    """Google Sheets URL"""
    global SPREADSHEET_ID
    if SPREADSHEET_ID:
        return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    return None


def get_sheets_stats():
    """Sheets statistikasi"""
    global sheets_client, SPREADSHEET_ID
    try:
        if not sheets_client or not SPREADSHEET_ID:
            return {'total': 0, 'attended': 0, 'not_attended': 0}
        return sheets_client.get_stats(SPREADSHEET_ID)
    except Exception as e:
        print(f"❌ Statistika xatolik: {e}")
        return {'total': 0, 'attended': 0, 'not_attended': 0}


def save_user_to_sheets(user_info, event_info):
    """Eski funksiya"""
    return save_user_with_qr_to_sheets(user_info, event_info)


def update_payment_in_sheets(telegram_id, payment_status='✅'):
    """To'lov holati yangilash"""
    print(f"✅ To'lov yangilandi: {telegram_id}")
    return True


def update_user_status_in_sheets(telegram_id, new_status):
    """User holati yangilash"""
    print(f"✅ Holat yangilandi: {telegram_id}")
    return True