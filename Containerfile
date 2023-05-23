FROM python:3.7-alpine
COPY . /app
WORKDIR /app
RUN pip install .
CMD ["gato_of_the_day"]
