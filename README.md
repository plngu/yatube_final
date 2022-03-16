# Проект Yatube

Социальная сеть

### Возможности

- Регистрация, страница профиля;
- возможность публикации постов с картинками;
- добавления поста к определенной группе;
- оставлять комментарии к посту;
- возможность подписки на авторов.

### Технологии

- Python3.9;
- Django 2.2.

### Приложения

- about (информация о проекте);
- core (кастомные страницы ошибок);
- posts (основная логика проекта, models, urls, views);
- users (логика авторизации, регистрации прользователей).

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/plngu/yatube_final.git
cd yatube_final
```

Cоздать и активировать виртуальное окружение:


```
python -m venv venv
source venv/Scripts/activate
```
Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
python pip install -r requirments.txt
```

Сделать миграции и запустить проект:
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
