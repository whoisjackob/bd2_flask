FROM python:latest

EXPOSE 5000

WORKDIR /app

COPY * /app/

RUN pip install -r requirements.txt

CMD ["flask", "run", "-h", "0.0.0.0", "-p", "5000"]