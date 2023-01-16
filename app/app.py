from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
from loguru import logger
from itertools import chain

import os  # provides ways to access the Operating System and allows us to read the environment variables

load_dotenv()

app = Flask(__name__)

uri = os.getenv("URI")
driver = GraphDatabase.driver(uri)

# Create labels for Employee and Department [works]
@app.route("/create_labels", methods=["GET"])
def create_labels():
    with driver.session() as session:
        session.run("CREATE (:Employee)")
        session.run("CREATE (:Department)")
    return "Labels created!"


# Create relationships between Employee and Department [works]
@app.route("/create_relationships", methods=["GET"])
def create_relationships():
    with driver.session() as session:
        session.run("MATCH (e:Employee),(d:Department) CREATE (e)-[:WORKS_IN]->(d)")
        session.run("MATCH (e:Employee),(d:Department) CREATE (e)-[:MANAGES]->(d)")
    return "Relationships created!"


# Add data to the database [works]
@app.route("/add_data", methods=["GET"])
def add_data():
    with driver.session() as session:
        session.run("CREATE (:Employee {name: 'John Doe', title: 'Manager'})")
        session.run("CREATE (:Employee {name: 'Jane Smith', title: 'Developer'})")
        session.run("CREATE (:Employee {name: 'Bob Johnson', title: 'Sales'})")
        session.run("CREATE (:Department {name: 'IT'})")
        session.run("CREATE (:Department {name: 'Marketing'})")
        session.run("CREATE (:Department {name: 'Sales'})")
        session.run(
            "MATCH (e:Employee {name: 'John Doe'}), (d:Department {name: 'IT'}) CREATE (e)-[:WORKS_IN]->(d)"
        )
        session.run(
            "MATCH (e:Employee {name: 'Jane Smith'}), (d:Department {name: 'IT'}) CREATE (e)-[:WORKS_IN]->(d)"
        )
        session.run(
            "MATCH (e:Employee {name: 'Bob Johnson'}), (d:Department {name: 'Sales'}) CREATE (e)-[:WORKS_IN]->(d)"
        )
        session.run(
            "MATCH (e:Employee {name: 'John Doe'}), (d:Department {name: 'IT'}) CREATE (e)-[:MANAGES]->(d)"
        )
    return "Data added!"


# Get all employees and optionally filter by name, title, and sort by name or title [works]
@app.route("/employees", methods=["GET"])
def get_employees():
    name = request.args.get("name")
    title = request.args.get("title")
    sort = request.args.get("sort")
    order = request.args.get("order")
    query = "MATCH (e:Employee)"
    if name:
        query += f" WHERE e.name =~ '(?i).*{name}.*'"
    if title:
        if name:
            query += f" AND e.title =~ '(?i).*{title}.*'"
        else:
            query += f" WHERE e.title =~ '(?i).*{title}.*'"
    if sort:
        query += f" ORDER BY e.{sort} {order}"
    query += " RETURN e AS e, id(e) AS id"
    with driver.session() as session:
        result = session.run(query)
        x = [
            dict(
                chain.from_iterable(
                    d.items() for d in (record["e"], {"id": record["id"]})
                )
            )
            for record in result.data()
            if record["e"] != {}
        ]
        return jsonify(x)


# Add a new employee
@app.route("/employees", methods=["POST"])
def add_employee():
    data = request.get_json()
    name = data.get("name")
    title = data.get("title")
    department = data.get("department")
    if not name or not title or not department:
        return jsonify({"error": "Missing required data"}), 400
    with driver.session() as session:
        result = session.run(f"MATCH (e:Employee) WHERE e.name = '{name}' RETURN e")
        if result.single():
            return jsonify({"error": "Employee already exists"}), 400
        session.run(f"CREATE (:Employee {{name: '{name}', title: '{title}'}})")
        session.run(
            f"MATCH (e:Employee), (d:Department) WHERE e.name = '{name}' AND d.name = '{department}' CREATE (e)-[:WORKS_IN]->(d)"
        )
        return jsonify({"message": "Employee added successfully"})


# Update an employee [works]
@app.route("/employees/<id>", methods=["PUT"])
def update_employee(id):
    data = request.get_json()
    name = data.get("name")
    title = data.get("title")
    department = data.get("department")
    with driver.session() as session:
        result = session.run(f"MATCH (e:Employee) WHERE ID(e) = {id} RETURN e")
        if not result.single():
            return jsonify({"error": "Employee not found"}), 404
        if name:
            session.run(f"MATCH (e:Employee) WHERE ID(e) = {id} SET e.name = '{name}'")
        if title:
            session.run(
                f"MATCH (e:Employee) WHERE ID(e) = {id} SET e.title = '{title}'"
            )
        if department:
            session.run(
                f"MATCH (e:Employee)-[r:WORKS_IN]->(d:Department) WHERE ID(e) = {id} DELETE r"
            )
            session.run(
                f"MATCH (e:Employee), (d:Department) WHERE ID(e) = {id} AND d.name = '{department}' CREATE (e)-[:WORKS_IN]->(d)"
            )
        return jsonify({"message": "Employee updated successfully"})


# Delete an employee [in progress]
@app.route("/employees/<id>", methods=["DELETE"])
def delete_employee(id):
    with driver.session() as session:
        result = session.run(f"MATCH (e:Employee) WHERE ID(e) = {id} RETURN e")
        if not result.single():
            return jsonify({"error": "Employee not found"}), 404
        result = session.run(
            f"MATCH (e:Employee)-[r:MANAGES]->(d:Department) WHERE ID(e) = {id} RETURN d"
        )
        if result.single():
            department = result.single()["d"].properties["name"]


# List of subordinates [works]
@app.route("/employees/<id>/subordinates", methods=["GET"])
def get_subordinates(id):
    with driver.session() as session:
        result = session.run(
            f"MATCH (e:Employee)-[r:MANAGES]->(s:Employee) WHERE ID(e) = {id} RETURN s"
        )
        subordinates = []
        for record in result:
            subordinates.append(record["s"].properties)
        return jsonify(subordinates)


# All departments with filtering and sorting [in_progress]
@app.route("/departments", methods=["GET"])
def get_departments():
    name = request.args.get("name")
    order_by = request.args.get("order_by")
    order = request.args.get("order")
    query = "MATCH (d:Department) "
    if name:
        query += f"WHERE d.name = '{name}' "
    query += "RETURN d as d, id(d) AS id"
    if order_by:
        query += f" ORDER BY d.{order_by} "
    if order:
        query += f" {order}"
    with driver.session() as session:
        result = session.run(query)
        x = [
            dict(
                chain.from_iterable(
                    d.items() for d in (record["d"], {"id": record["id"]})
                )
            )
            for record in result.data()
            if record["d"] != {}
        ]
        return jsonify(x)


# Employees in a department
@app.route("/departments/<id>/employees", methods=["GET"])
def get_department_employees(id):
    with driver.session() as session:
        result = session.run(
            f"MATCH (d:Department)-[r:WORKS_IN]->(e:Employee) WHERE ID(d) = {id} RETURN e as e, id(e) as id"
        )
        x = [
            dict(
                chain.from_iterable(
                    d.items() for d in (record["e"], {"id": record["id"]})
                )
            )
            for record in result.data()
            if record["e"] != {}
        ]
        return jsonify(x)


if __name__ == "__main__":
    app.run()
