<div align="center">

🛡️ Real-Time AI Anti-Spam System 🛡️
A multi-service, server-side application designed to detect and filter spam, phishing, and malicious content in real-time using a microservices architecture, a live threat intelligence database, and a powerful Large Language Model (LLM).

</div>

<p align="center">
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" alt="RabbitMQ"/>
<img src="https://img.shields.io/badge/redis-%23DD0031.svg?&style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/>
<img src="https://img.shields.io/badge/docker-%230db7ed.svg?&style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
<img src="https://img.shields.io/badge/Gemini_API-4285F4?style=for-the-badge&logo=google-gemini&logoColor=white" alt="Gemini API"/>
</p>

✨ Core Features
This system provides a robust defense against malicious content by combining multiple layers of analysis:

LLM-Powered Content Analysis: Utilizes the Google Gemini API for deep contextual understanding of text to identify sophisticated phishing attempts and scams that keyword-based systems would miss.

Live Reputation Database: Leverages Redis for a high-speed, dynamic blocklist of malicious domains, IPs, and keywords.

Proactive Threat Intelligence: A dedicated background service continuously fetches data from public threat intelligence feeds, ensuring the reputation database is always up-to-date with emerging threats.

Resilient & Scalable Architecture: Built on a microservices model using RabbitMQ, ensuring that components are decoupled and can be scaled independently.

🏗️ System Architecture
The application follows a message-driven microservices pattern, ensuring high throughput and resilience.

                               +-----------------------------+
[Public Threat Feeds]--------->| Threat Intel Ingestion Svc. |
                               +-----------------------------+
                                             | (writes to)
                                             v
                                     +---------------+
                                     | Redis DB      | (Live Reputation)
                                     +---------------+
                                             ^
                                             | (reads from)
                                             |
[Incoming Content]--->[Ingestion API]--->[Queue]--->[Combined Intelligence Worker]

🛠️ Components
Ingestion API (main.py): A lightweight FastAPI server that acts as the public-facing entry point. It validates incoming data and places it onto the RabbitMQ queue for processing.

Combined Intelligence Worker (worker.py): The core of the system. This worker consumes messages from the queue and performs a multi-layered analysis, combining evidence from the live Redis blocklist and the Gemini API to make a final, accurate verdict.

Threat Intel Worker (threat_intel_worker.py): A proactive background service that runs independently. It periodically fetches data from external threat intelligence feeds and updates the Redis reputation database.

🚀 Getting Started
Follow these instructions to get the full system running on your local machine.

Prerequisites
Python 3.8+

Docker

A Gemini API Key from Google AI Studio

Installation & Setup
Clone the repository:

git clone https://github.com/your-username/realtime-ai-spam-filter.git
cd realtime-ai-spam-filter

Create a requirements.txt file in your project folder with the following content:

fastapi
uvicorn[standard]
pika
redis
requests

Install Python dependencies:

pip install -r requirements.txt

Add your Gemini API Key:
Open the worker.py file and paste your API key into the apiKey variable:

# worker.py
apiKey = "PASTE_YOUR_GEMINI_API_KEY_HERE"

Running the System
You will need three separate terminals open in your project directory to run the full system.

Start Backend Services (RabbitMQ & Redis):
In one of your terminals, run the Docker commands to start the message queue and the database:

# Start RabbitMQ
docker run -d --name project2-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Start Redis
docker run -d --name project3-redis -p 6379:6379 redis

Run the Threat Intelligence Worker:
In your first terminal, start the threat intel script. Let it run for a minute to populate the database.

python threat_intel_worker.py

Run the Combined Intelligence Worker:
In your second terminal, start the main AI worker. It will connect to RabbitMQ and Redis.

python worker.py

Run the API Server:
In your third terminal, start the FastAPI server.

uvicorn main:app --reload

Your full anti-spam system is now running! You can send test messages to the API endpoint (http://127.0.0.1:8000/analyze) via the interactive docs and monitor the analysis in your worker terminals.
