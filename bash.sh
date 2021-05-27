#!/bin/bash

cd /app/projet/MO && flask run&
cd /app/router/ && python3 app.py&
cd /app/projet/ && rasa run actions --auto-reload&
cd /app/projet/ && rasa run --enable-api --cors "*" -m ./models/ --endpoints endpoints.yml&
cd /app/projet_fr/ && rasa run --enable-api --cors "*" -m ./models/ --endpoints endpoints.yml -p 5006&
cd /app/projet_tn/ && rasa run --enable-api --cors "*" -m ./models/ --endpoints endpoints.yml -p 5007
