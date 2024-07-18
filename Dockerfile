# 
FROM python:3.9

# 
WORKDIR /app

# 
COPY ./requirements.txt /app/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 
COPY . /app

#
RUN mkdir -p service_accounts

#
EXPOSE 8080

# 
CMD ["flask", "run", "-h", "0.0.0.0", "-p", "8080"]
