# Employees and Departments REST API with Neo4j database

## Getting Started

All endpoints are available and described in the app.py file  
First 3 endpoints were used to load some data and create relationships, you don't have to use them again.
You can run the app using `docker-compose up --build` command and point requests to `localhost:5000`.

## Add a new Employee

    curl -X POST http://localhost:5000/employees -H "Content-Type: application/json" -d '{"name": "Jakub Szczepanski", "title": "Developer", "department": "IT"}'

## Get all Employees

    curl -X GET http://localhost:5000/employees

To use filter on all endpoints 

    curl -X GET http://localhost:5000/employees?title=Developer

## Update an Employee

    curl -X PUT http://localhost:5000/employees/<id> -H "Content-Type: application/json" -d '{"name": "Kuba Szczepanski"}'

## Delete an Employee

    curl -X DELETE http://localhost:5000/employees/<id>

## List of subordinates

    curl -X GET http://localhost:5000/employees/<id>/subordinates

## List of Departments

    curl -X GET http://localhost:5000/departments

## Employees in a department 

    curl -X GET http://localhost:5000/departments/<id>/employees