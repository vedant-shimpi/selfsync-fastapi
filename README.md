This project is owned by Digikore studio limited

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload # run code uvicorn main:app --host 0.0.0.0 --port 8000 --reload

