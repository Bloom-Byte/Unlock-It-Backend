# Unlock-It-Backend
Django Api Backend for Unlock-It.

Unlock IT is an application that allows users to upload their files and sell them for a price. They can send this link to sell to friends or post on their social media page.

The API uses AWS S3 for file storage and distribution, scalable storage size, and 99.99% worldwide availability.

## Development

1. Install docker
2. Create a new .env file, copy over the keys from .env.example and set the values for the keys. Some keys have values assigned to them already, you can leave them as they are
3. Run `docker compose build`
4. Run `docker compose up`
5. To stop the server, run `docker compose down`


Upon starting the server, navigate to http://localhost:8000 to test out the simple interface

An API Documentation is located at http://localhost:8000/docs/
