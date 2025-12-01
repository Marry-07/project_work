from flask import Flask, request, jsonify 
from flask_sqlalchemy import SQLAlchemy # связь базы данных с flask
import os # модуль, для работы с переменными окружения

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv( # ключ, который ожидает flask_sqlalchemy для подключения к базе данных
    'DATABASE_URL',
    'postgresql://postgres:postgres@db:5432/tourdb'
    # postgresql:// — диалект PostgreSQL; postgres:postgres — логин/пароль; db:5432 — хост (вероятно, имя контейнера Docker db) и порт; tourdb — имя базы
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) # объект бд


# Модель — класс Python, который соответствует таблице в базе данных

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    time = db.Column(db.DateTime, server_default=db.func.now())


# Маршруты

# декоратор @app.route 
@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json() or {}

    # Читаем поля из JSON
    name = data.get('name')
    email = data.get('email')
    service = data.get('service', 'tour')
    if not name or not email:
        return jsonify({'error': 'name and email required'}), 400
    booking = Booking(name=name, email=email, service=service)
    db.session.add(booking) # добавляем объект SQLAlchemy
    db.session.commit()
    return jsonify({'id': booking.id, 'status': 'created'}), 201


# список бронирований
@app.route('/api/bookings', methods=['GET'])
def list_bookings():
    # Booking.query - интерфейс SQLAlchemy для запросов. Возвращает Query-объект.

    rows = Booking.query.order_by(Booking.time.desc()).limit(50).all()
    return jsonify([{'id': r.id, 'name': r.name, 'email': r.email, 'service': r.service} for r in rows]) # Возвращается JSON-массив объектов с выбранными полями


# запуск
if __name__ == '__main__': # запустить код только если файл выполняется как скрипт, а не импортируется как модуль.
    with app.app_context(): # создаем контекст - нужен для доступа к конфигурациям
        db.create_all() # Создаёт в базе таблицы, соответствующие моделям (если их нет)
    app.run(host='0.0.0.0', port=8000)
