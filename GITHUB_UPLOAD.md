# Как загрузить проект на GitHub

## 1. Создать репозиторий

На GitHub создать новый репозиторий с названием:

```text
Vk
```

## 2. Открыть терминал в папке проекта

```bash
cd путь_к_папке\Vk
```

## 3. Инициализировать git

```bash
git init
```

## 4. Добавить файлы

```bash
git add .
```

## 5. Сделать commit

```bash
git commit -m "Initial commit"
```

## 6. Подключить репозиторий GitHub

```bash
git remote add origin https://github.com/AnnaLyzhina/Vk.git
```

## 7. Загрузить проект

```bash
git branch -M main
git push -u origin main
```

## Важно

Перед загрузкой убедитесь, что файла `.env` нет в commit.

Проверить можно командой:

```bash
git status
```

Файл `.env` не должен отображаться в списке файлов для загрузки.