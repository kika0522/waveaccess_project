# waveaccess_project


### Установка и запуск 


#### Запустите сервисы с помощью docker-compose
```
docker-compose up --build -d
```

#### Доступные сервисы
FastAPI приложение: http://localhost:8000/docs

MinIO консоль: http://localhost:9001 (логин: minio, пароль: minio123)

Adminer (БД): http://localhost:8080 (server: postgres, username: postgres, password: pass1234, database: zip_db)

#### Остановка сервисов
```
docker-compose down
```
##### Для полной очистки
```
docker-compose down -v
```