# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Install system dependencies needed for pyaudio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
 && apt-get clean 

# 3. Set the working directory
WORKDIR /app

# 4. Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . .

# 6. Expose the port on which Streamlit will run
EXPOSE 8080

# 7. Set environment variables
ENV PORT=8080

# 8. Run the Streamlit app using the shell for variable substitution
CMD ["/bin/sh", "-c", "streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0"]
