#!/usr/bin/env python3
#Author Sunil Sankar
#Date 29-Sep-2025
import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine

app = Flask(__name__)

# ---------- SQL Server connection ----------
# Required envs: DBUSER, DBPASS, DBHOST, DBNAME
# Optional: DBPORT (defaults to 1433)
DBUSER = os.environ["DBUSER"]
DBPASS = os.environ["DBPASS"]
DBHOST = os.environ["DBHOST"]           # e.g. "sqlserver.company.local" or "10.0.0.5"
DBPORT = os.environ.get("DBPORT", "1433")
DBNAME = os.environ["DBNAME"]

# Note: spaces in the driver name must be URL-encoded as +
# Encrypt/TrustServerCertificate can be adjusted to your security posture.
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mssql+pyodbc://{DBUSER}:{DBPASS}"
    f"@tcp:{DBHOST},{DBPORT}/{DBNAME}"
    f"?driver=ODBC+Driver+18+for+SQL+Server"
    f"&Encrypt=yes&TrustServerCertificate=yes"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Optional: speed up executemany (bulk) with pyodbc
@event.listens_for(Engine, "before_cursor_execute")
def _enable_fast_executemany(conn, cursor, statement, parameters, context, executemany):
    try:
        if executemany and hasattr(cursor, "fast_executemany"):
            cursor.fast_executemany = True
    except Exception:
        # Non-pyodbc drivers or older pyodbc versions will just skip this.
        pass


# ---------- Model ----------
class InventoriesModel(db.Model):
    __tablename__ = "inventories"

    id = db.Column(db.Integer, primary_key=True)  # -> IDENTITY(1,1) in MSSQL
    hostname = db.Column(db.String(255), nullable=False)
    environment = db.Column(db.String(255))
    ipaddress = db.Column(db.String(255))
    applicationname = db.Column(db.String(255))

    def __repr__(self):
        return f"<Inventory {self.hostname}>"


# ---------- App startup hook ----------
@app.before_first_request
def init_db():
    # If you use Flask-Migrate/Alembic, prefer running migrations instead.
    db.create_all()
    db.session.commit()


# ---------- Routes ----------
@app.route("/")
def hello():
    return {"message": "This is an inventory service"}

@app.route("/inventories", methods=["POST", "GET"])
def handle_inventories():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            new_inventory = InventoriesModel(
                hostname=data["hostname"],
                environment=data.get("environment"),
                ipaddress=data.get("ipaddress"),
                applicationname=data.get("applicationname"),
            )
            db.session.add(new_inventory)
            db.session.commit()
            return {"message": f"inventory {new_inventory.hostname} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}, 400

    # GET
    inventories = InventoriesModel.query.all()
    results = [
        {
            "hostname": inv.hostname,
            "environment": inv.environment,
            "ipaddress": inv.ipaddress,
            "applicationname": inv.applicationname,
        }
        for inv in inventories
    ]
    return {"count": len(results), "inventories": results, "message": "success"}

@app.route("/inventories/<int:inventory_id>", methods=["GET", "PUT", "DELETE"])
def handle_inventory(inventory_id):
    inventory = InventoriesModel.query.get_or_404(inventory_id)

    if request.method == "GET":
        response = {
            "hostname": inventory.hostname,
            "environment": inventory.environment,
            "ipaddress": inventory.ipaddress,
            "applicationname": inventory.applicationname,
        }
        return {"message": "success", "inventory": response}

    if request.method == "PUT":
        data = request.get_json()
        inventory.hostname = data["hostname"]
        inventory.environment = data["environment"]
        inventory.ipaddress = data["ipaddress"]
        inventory.applicationname = data["applicationname"]
        db.session.add(inventory)
        db.session.commit()
        return {"message": f"inventory {inventory.hostname} successfully updated"}

    # DELETE
    db.session.delete(inventory)
    db.session.commit()
    return {"message": f"inventory {inventory.hostname} successfully deleted."}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
