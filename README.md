Event Management & RSVP System🚀🚀
Overview📝
This project is a full-stack Event Management & RSVP System, allowing users to register for events, receive automated email reminders, and check in via QR codes. It is built using Django, PostgreSQL, Celery, Redis, and Bootstrap to ensure efficient management and seamless user experience.

Features📱
  ->Event Creation & Management – Organizers can create events and manage RSVPs.
  ->RSVP System – Users can register for events and receive confirmation emails.
  ->Automated Email Reminders – Celery + Redis handle scheduled email notifications.
  ->Event Dashboard – Includes filters for efficient event tracking.

QR Code Check-in (Bonus feature) 
  –> Enables seamless attendee check-ins.⬜

Technologies Used⚒️
  ->Backend: Django (Web framework), PostgreSQL (Database)
  ->Frontend: Bootstrap (Responsive UI)
  ->Task Scheduling: Celery + Redis (Email automation)
  ->Authentication & Security: Django Authentication

Setup & Installation✏️
  Clone this repository:
    git clone https://github.com/your-repo/event-management.git
    cd event-management
Install dependencies:👩‍🏫
  pip install -r requirements.txt
    Set up PostgreSQL and apply migrations:

  python manage.py migrate
    Start the Django server:

  python manage.py runserver
    Run Celery worker & Redis server:

  celery -A project worker --loglevel=info
    redis-server

  
Usage🌈
  ->Create and manage events via the admin panel.
  ->Users can RSVP and receive confirmation emails automatically.
  ->Event organizers can monitor RSVP lists via the dashboard.
  ->QR code check-in (if implemented) enhances entry management.
