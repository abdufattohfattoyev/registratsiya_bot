from utils.db_api.database import Database


class EventManager:
    def __init__(self, db_path="db/bot_database.db"):
        self.db = Database(db_path)

    def add_event(self, name_uz, name_ru, name_en, date, time, address_uz, address_ru, address_en, payment_amount):
        """Yangi tadbir qo'shish"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE events SET is_active = 0')
            cursor.execute(
                '''
                INSERT INTO events (name_uz, name_ru, name_en, date, time, address_uz, address_ru, address_en, payment_amount, is_active) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''',
                (name_uz, name_ru, name_en, date, time, address_uz, address_ru, address_en, payment_amount)
            )
            event_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Yangi tadbir qo'shildi: {name_uz} (ID: {event_id})")
            return event_id

    def get_active_event(self, lang='uz'):
        """Faol tadbirni tilga qarab olish"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            name_field = f'name_{lang}'
            address_field = f'address_{lang}'
            cursor.execute(f'''
                SELECT id, {name_field}, date, time, {address_field}, payment_amount, is_active, created_at
                FROM events 
                WHERE is_active = 1 
                ORDER BY date ASC, time ASC 
                LIMIT 1
            ''')
            return cursor.fetchone()

    def get_all_active_events(self, lang='uz'):
        """Barcha faol tadbirlarni tilga qarab olish"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            name_field = f'name_{lang}'
            address_field = f'address_{lang}'
            cursor.execute(f'''
                SELECT id, {name_field}, date, time, {address_field}, payment_amount, is_active, created_at
                FROM events 
                WHERE is_active = 1 
                ORDER BY date ASC, time ASC
            ''')
            return cursor.fetchall()

    def get_event_by_id(self, event_id, lang='uz'):
        """ID orqali tadbirni tilga qarab olish"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            name_field = f'name_{lang}'
            address_field = f'address_{lang}'
            cursor.execute(f'''
                SELECT id, {name_field}, date, time, {address_field}, payment_amount, is_active, created_at
                FROM events 
                WHERE id = ?
            ''', (event_id,))
            return cursor.fetchone()

    def update_event(self, event_id, lang='uz', name=None, date=None, time=None, address=None, payment_amount=None):
        """Tadbirni tahrirlash"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if name:
                updates.append(f'name_{lang} = ?')
                params.append(name)
            if date:
                updates.append('date = ?')
                params.append(date)
            if time:
                updates.append('time = ?')
                params.append(time)
            if address:
                updates.append(f'address_{lang} = ?')
                params.append(address)
            if payment_amount is not None:
                updates.append('payment_amount = ?')
                params.append(payment_amount)
            if updates:
                params.append(event_id)
                query = f'UPDATE events SET {", ".join(updates)} WHERE id = ?'
                try:
                    cursor.execute(query, params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        print(f"✅ Tadbir yangilandi: {event_id}")
                        return True
                    else:
                        print(f"❌ Tadbir topilmadi: {event_id}")
                        return False
                except Exception as e:
                    print(f"❌ Tadbir yangilashda xatolik: {e}")
                    return False
            return False

    def toggle_event_status(self, event_id):
        """Marosim holatini o'zgartirish"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT is_active FROM events WHERE id = ?", (event_id,))
                current_status = cursor.fetchone()
                if not current_status:
                    print(f"❌ Tadbir topilmadi: {event_id}")
                    return False
                is_currently_active = bool(current_status[0])
                if is_currently_active:
                    cursor.execute("UPDATE events SET is_active = 0 WHERE id = ?", (event_id,))
                    print(f"✅ Tadbir nofaol qilindi: {event_id}")
                else:
                    cursor.execute("UPDATE events SET is_active = 0")
                    cursor.execute("UPDATE events SET is_active = 1 WHERE id = ?", (event_id,))
                    print(f"✅ Tadbir faol qilindi: {event_id}")
                conn.commit()
                return True
            except Exception as e:
                print(f"❌ Tadbir holatini o'zgartirishda xatolik: {e}")
                return False

    def get_events_with_stats(self, lang='uz'):
        """Marosimlar va ularning statistikasi"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            name_field = f'name_{lang}'
            address_field = f'address_{lang}'
            cursor.execute(f'''
                SELECT id, {name_field}, date, time, {address_field}, payment_amount, is_active, created_at
                FROM events 
                ORDER BY id DESC
            ''')
            events = cursor.fetchall()
            events_with_stats = []
            for event in events:
                event_id = event[0]
                cursor.execute('SELECT COUNT(*) FROM users WHERE event_id = ?', (event_id,))
                total = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM users WHERE event_id = ? AND payment_status = "paid"', (event_id,))
                paid = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM users WHERE event_id = ? AND approved = 1', (event_id,))
                approved = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM users WHERE event_id = ? AND attended = 1', (event_id,))
                attended = cursor.fetchone()[0]
                cursor.execute(
                    'SELECT COUNT(*) FROM users WHERE event_id = ? AND payment_status = "paid" AND approved = 0',
                    (event_id,))
                pending = cursor.fetchone()[0]
                event_dict = {
                    'id': event[0],
                    'name': event[1],
                    'date': event[2],
                    'time': event[3],
                    'address': event[4],
                    'payment_amount': event[5],
                    'is_active': bool(event[6]),
                    'created_at': event[7],
                    'stats': {
                        'total': total,
                        'paid': paid,
                        'approved': approved,
                        'attended': attended,
                        'pending': pending
                    }
                }
                events_with_stats.append(event_dict)
            return events_with_stats

    def debug_events_status(self):
        """Debug: barcha marosimlar holatini ko'rsatish"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name_uz, is_active FROM events ORDER BY id")
            events = cursor.fetchall()
            print("=== DEBUG: MAROSIMLAR HOLATI ===")
            for event in events:
                status = "FAOL" if event[2] else "NOFAOL"
                print(f"ID: {event[0]} | {event[1]} | is_active={event[2]} | {status}")
            cursor.execute("SELECT COUNT(*) FROM events WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            print(f"Database'da faol marosimlar soni: {active_count}")
            return events