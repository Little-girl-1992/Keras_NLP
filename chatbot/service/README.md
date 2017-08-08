chatbot service

## Build environment for chatbot service 

    make sure your python version is 2.7 or later
    pip install -r requirements.txt

## Start server
    ### Using django server

        1. copy word embedding vector file to chatbot/rankingsvm/data/ 
        2. /path/to/python manage.py runserver 0.0.0.0:8080
    ### Issue query from client
        /path/to/python client.py "Chatbot，你好！"
