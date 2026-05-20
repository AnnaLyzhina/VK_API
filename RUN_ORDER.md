# В какой последовательности запускать проект

Эта инструкция нужна для первого запуска проекта на компьютере.

## 1. Открыть папку проекта

Откройте в VS Code папку `Vk`.

В терминале нужно находиться в папке, где лежит `main.py`.

Проверить можно командой:

```bash
dir
```

В списке должен быть файл:

```text
main.py
```

---

## 2. Создать виртуальное окружение

```bash
python -m venv venv
```

---

## 3. Активировать виртуальное окружение

PowerShell:

```bash
venv\Scripts\activate
```

Если PowerShell выдаёт ошибку безопасности:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Потом повторить:

```bash
venv\Scripts\activate
```

Если всё получилось, слева появится:

```text
(venv)
```

---

## 4. Обновить pip

```bash
python -m pip install --upgrade pip
```

---

## 5. Установить зависимости

```bash
pip install -r requirements.txt
```

В этом проекте нет SQLAlchemy, поэтому ошибок сборки SQLAlchemy быть не должно.

---

## 6. Создать файл .env

Скопировать:

```text
.env.example
```

и назвать копию:

```text
.env
```

Заполнить:

```env
TOKEN=токен_группы_vk
USER_TOKEN=токен_пользователя_vk
GROUP_ID=id_группы
DB_NAME=vk
DB_USER=postgres
DB_PASSWORD=пароль_postgresql
DB_HOST=localhost
DB_PORT=5432
```

---

## 7. Создать базу PostgreSQL

В DBeaver или pgAdmin выполнить:

```sql
CREATE DATABASE vk;
```

---

## 8. Создать таблицы

Запустить один раз:

```bash
python db/create_tables.py
```

---

## 9. Проверить код линтером

Необязательно для запуска, но полезно перед сдачей:

```bash
flake8 .
```

---

## 10. Запустить бота

```bash
python main.py
```

Должно появиться:

```text
Bot started...
```

---

## 11. Проверить работу в VK

После запуска `python main.py` бот не открывает браузер.

Нужно вручную зайти во ВКонтакте:

1. открыть свою группу;
2. открыть сообщения группы;
3. написать боту: `Привет`.

---

## Краткая шпаргалка команд

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python db/create_tables.py
python main.py
```