FROM python:3.12-slim

WORKDIR /code

# Install requirements
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application files
COPY ./src /code/src

# Hugging Face Spaces requires running on port 7860 by default
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
