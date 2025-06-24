-- Create the database
CREATE DATABASE event_db;

-- Create a user for the application
CREATE USER event_user WITH PASSWORD 'event_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE event_db TO event_user;

-- Connect to the database
\c event_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO event_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO event_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO event_user;
