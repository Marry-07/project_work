from flask import Flask, request, jsonify # создание веб-сервера, можем получать данные с методом POST и вспомогательная функция,
# которая преобразует Python-структуры (словарь, список) в JSON-ответ, выставляет правильный Content-Type: application/json и кодирует в UTF-8.
from flask_sqlalchemy import SQLAlchemy # связь базы данных с flask
import os # модуль, для работы с переменными окружения

app = Flask(__name__) # создание экземпляра приложения, инициализирует приложение, регистрирует исключения, маршруты, конфиг
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv( # ключ, который ожидает flask_sqlalchemy для подключения к базе данных. Значение — строка подключения (URI) к СУБД
    'DATABASE_URL',
    'postgresql://postgres:postgres@db:5432/tourdb' # читаем переменную окружения DATABASE_URL; если она не задана, используем значение по умолчанию
    # postgresql:// — диалект PostgreSQL; postgres:postgres — логин/пароль; db:5432 — хост (вероятно, имя контейнера Docker db) и порт; tourdb — имя базы
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # можем выполнять настройки с базой данных

db = SQLAlchemy(app) # создаем объект бд. автоматически конфигурирует по app.config['SQLALCHEMY_DATABASE_URI']


# описание модели бронирования

# Модель — класс Python, который соответствует таблице в базе данных
# Наследуется от db.Model, поэтому SQLAlchemy знает как маппить этот класс на таблицу

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.BigInteger, primary_key=True) # первичный ключ, уникальный, автоматом проставляется
    name = db.Column(db.String(100), nullable=False) # без пустых/нулевых строк
    email = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100), nullable=False) # тип услуги
    time = db.Column(db.DateTime, server_default=db.func.now()) # если не передать time при вставке, СУБД сама поставит текущее время.


# Маршруты !!!!

# Flask использует декоратор @app.route для связывания URL с функцией-обработчиком
@app.route('/health')
def health():
    return jsonify({'status': 'ok'}) # типа работает ли сервер


# создание бронирования
@app.route('/api/bookings', methods=['POST']) # URL для создания ресурса. По REST-конвенции POST на коллекцию /api/bookings создаёт новый ресурс (booking)
def create_booking():
    data = request.get_json() or {} # парсит JSON-тело запроса в Python-словарь. Если тело пустое или не JSON, вернёт None

    # Читаем необходимые поля из JSON
    name = data.get('name')
    email = data.get('email')
    service = data.get('service', 'tour') # если сервис отсутствует - по умолчанию - tour
    if not name or not email:
        return jsonify({'error': 'name and email required'}), 400 # ошибка в HTTP и JSON
    booking = Booking(name=name, email=email, service=service) # создаем объект модели
    db.session.add(booking) # добавляем объект в текущую сессию SQLAlchemy
    db.session.commit() # добавит все нужное и сохранит в таблицу
    return jsonify({'id': booking.id, 'status': 'created'}), 201


# список бронирований
@app.route('/api/bookings', methods=['GET'])
def list_bookings():
    # Booking.query - интерфейс SQLAlchemy для запросов. Возвращает Query-объект.
    # order_by(Booking.created_at.desc()) — сортировка по created_at в порядке убывания (новые брони вверху).

    # .limit(50) — ограничиваем результат 50 записями (защита от выдачи всех записей сразу).
    # .all() — выполняет SQL и возвращает список объектов Booking.
    rows = Booking.query.order_by(Booking.time.desc()).limit(50).all()
    return jsonify([{'id': r.id, 'name': r.name, 'email': r.email, 'service': r.service} for r in rows]) # Возвращается JSON-массив объектов с выбранными полями


# запуск
if __name__ == '__main__': # запустить код только если файл выполняется как скрипт, а не импортируется как модуль.
    with app.app_context(): # создаем контекст - нужен для доступа к конфигурациям
        db.create_all() # Создаёт в базе таблицы, соответствующие моделям (если их нет)
    app.run(host='0.0.0.0', port=8000) # запускает встроенный сервер
    # host - доступ из сети, по умолчанию Flask слушает 127.0.0.1 - только локально.
