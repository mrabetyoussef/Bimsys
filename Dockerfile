FROM python:3.12

WORKDIR /bimsys

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python3", "run.py"]
