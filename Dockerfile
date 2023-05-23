# Dockerfile to setup python for flask
from python:3.10-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app

COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

ENV PORT 8000
ENV DEBUG False

# Make port 80 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
# use wsgi server
# cd /app
WORKDIR /app/src
CMD ["flask", "run"]
