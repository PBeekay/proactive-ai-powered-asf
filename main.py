from fastapi import FastAPI
from pydantic import BaseModel
import pika  # The Python library for RabbitMQ
import json  # To convert our data to a string
from pika.exceptions import AMQPConnectionError

# --- 2. Define data structure ---
class Message(BaseModel):
    content: str

# --- 3. Create FastAPI app ---
app = FastAPI()

# --- 4. Define the function to publish to the queue ---
def send_to_queue(message_body: str):
    """Connects to RabbitMQ and sends a message."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='task_queue', durable=True)

        # Publish the message to the queue
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
            ))
        
        print(f" [x] Sent message to queue: {message_body}")
        connection.close()
        return True
    except AMQPConnectionError:
        print(" [!] Error: Could not connect to RabbitMQ.")
        return False

# --- 5. API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API Publisher is running!"}

@app.post("/analyze")
def analyze_content(message: Message):
    """Receives a message and sends it to the RabbitMQ queue."""
    # Convert the message object to a JSON string
    message_json = json.dumps(message.dict())
    
    if send_to_queue(message_json):
        return {"status": "message_queued"}
    else:
        return {"status": "error", "detail": "Could not queue message."}
