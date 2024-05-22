from flask import Flask, jsonify, request # imports the Flask class that gives us a bunch of tasty flask functionality
from flask_marshmallow import Marshmallow #create schema objects - determine the shape of the data we're sending and receiving
from marshmallow import fields, ValidationError # the necessary fields that we're accepting and the data types for those fields
# ValidationError is going to give us information on why our post or put wasnt succesful
# checking the incoming json data against our schema
import mysql.connector
from mysql.connector import Error



app = Flask(__name__) # creates a Flask app object that we store to the app variable
app.json.sort_keys = False

# we pass in the current file as the app location
ma = Marshmallow(app) #creates a marshmallow object that we can build schemas from

# creating a schema for customer data
# defining the shape of the json data that is coming in
# there are certain fields and types of those fields that need to be adhered to
class CustomerSchema(ma.Schema): 
    # we define the types of the fields for the incoming data
    # set constraints for that data - whether its required to pass the schema check or not
    name = fields.String(required=True) 
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        
        fields = ("name", "email", "phone", "customer_id") #the fields that we're grabbing information from the incoming data



# instantiating our CustomerSchema
customer_schema = CustomerSchema() #checking one single customer
customers_schema = CustomerSchema(many=True)#handling several rows of customer data

db_name = "e_commerce_db"
user = "root"
password = "Buttmuffin3!"
host = "localhost"

def get_db_connection():
    try:
        # attempt to make a connection
        conn = mysql.connector.connect(
            database=db_name,
            user=user,
            password=password,
            host=host
        )

        # check for a connection
        if conn.is_connected():
            print("Connected to db succesfully (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧")
            return conn
        
    except Error as e:
        # handling any errors specific to our Database
        print(f"Error: {e}")
        return None


# define the home page route
# @something <- decorator - provides additional functionality to any function immediately below it
@app.route('/') #a url location
# defining the functionality for that specific route
def home():
    return "Hello there! Thanks for comin to hang in my Flask Application (づ￣ 3￣)づ (￣o￣) . z Z"
# return in functions within a flask route is what gets rendered to the browser

# url location in route always needs to be a string
@app.route("/about")
def about():
    return "Hello my name is Ryan. I like to play super smash and eat cupcakes. also get rekt"

# make sure the endpoint names make sense. The location in the url is relevant to what functionality is being applied
# creating a route for a GET method
# HTTP Methods - GET, POST, PUT, DELETE
#           route location      HTTP method for that location
@app.route("/customers", methods = ["GET"]) #always methods and its always a list even if theres just one
def get_customers():
    # establish our db connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # we're handling python dictionaries that are converted from json data
    # gives a list of dictionaries

    # SQL query to retrieve all customer data from our database
    query = "SELECT * FROM Customers"

    # executing query
    cursor.execute(query)

    # fetch results and prepare them for the JSON response
    customers = cursor.fetchall()
    print(customers)

    # closing the db connection
    cursor.close()
    conn.close()
    

    # use Marshmallow to format our json response
    return customers_schema.jsonify(customers)


@app.route('/customers', methods=["POST"])
def add_customer():
    # validate and deserialize the incoming data using Marshmallow -sent by the client
    # deserialize - making readable to python as dictionary
    customer_data = customer_schema.load(request.json)
    # taking the request to this route, grabbing the json data, and turning into a python dictionary
    print(customer_data)

    # connect to our db
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # create new customer details to send to our db
    # the json data above
    # setting variables from our dictionary
    name = customer_data['name']
    email = customer_data['email']    
    phone = customer_data['phone']
    # new_customer tuple to insert into our db
    new_customer = (name, email, phone)
    print(new_customer)
    # SQL Query to insert data into our DB
    query = "INSERT INTO Customers(name, email, phone) VALUES (%s, %s, %s)"
    # executing the query
    cursor.execute(query, new_customer)
    conn.commit()

    # successfuly addition of the new cistomer
    cursor.close()
    conn.close()
    return jsonify({"message": "New customer was added succesfully"}), 201 #resrouces succesfully created

# using flask's dynamic routing to receive paramters through the url
@app.route("/customers/<int:id>", methods=["PUT"]) # PUT replace already existing data (or resource)
def update_customer(id):
    try: 
        # validating incoming data to make sure it adheres to our schema
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        print(f"Error: {e}")
        return jsonify(e.messages), 400 #bad request - the information we're sending doesnt meet the application standards
    
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500 #server error - when it doesnt know how to handle the error
        cursor = conn.cursor()

        # updated customer information
        name = customer_data['name']
        email = customer_data["email"]
        phone = customer_data["phone"]

        # query to update customer info with the id passed from the URL
        query = "UPDATE Customers SET name = %s, email = %s, phone = %s WHERE customer_id = %s"
        updated_customer = (name, email, phone, id)
        cursor.execute(query, updated_customer)
        conn.commit()

        # succesfully update a new customer
        return jsonify({"message": "Customer details updated successfully"}), 200 #successful connection

    except Error as e:
        print(f"Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500 # server error - issue connecting to the server that the server cannot handle
    
    finally:
        # closing connection and cursor
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# delete customer
@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500 #server error - when it doesnt know how to handle the error
        cursor = conn.cursor()
        customer_to_remove = (id,)

        # sql query to to check if customer exists
        query = "SELECT * FROM Customers WHERE customer_id = %s"
        cursor.execute(query, customer_to_remove)
        customer = cursor.fetchone() #retrieving one record
        # even the customer_id is a unique identifier so we'll only end up with one row regardless
        if not customer:
            return jsonify({"message": "Customer not found"}), 404 #not found - trying to delete a customer that does not exist
        
        # query to check if customer has an order
        query = "SELECT * FROM orders WHERE customer_id = %s"
        cursor.execute(query, customer_to_remove)
        orders = cursor.fetchall()
        if orders:
            return jsonify({"message": "Customer has associated orders, cannot delete"}), 400 #bad request - requesting to delete a customer that has associated orders
        # FINALLY If the customer exists and they dont have assoiciated orders we can delete them
        query = "DELETE FROM Customers WHERE customer_id = %s"
        cursor.execute(query, customer_to_remove)
        conn.commit()

        # Successful deletion
        return jsonify({"message": "Customer Removed Successfully"}), 200
    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

class OrderSchema(ma.Schema):
    order_id = fields.Int(dump_only=True) #only for exposing - read only
    customer_id = fields.Int(required=True)
    date = fields.Date(required=True)

    class Meta:
        fields = ("order_id", "customer_id", "date")  
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)  


# CREATE TWO Orders Routes
# route for adding an order using POST - consider how many orders you're creating or getting
# route for getting ALL orders using GET - to decide which schema to use

@app.route('/orders', methods=['POST'])
def add_order():
    try:
        # Validate and deserialize input
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        query = "INSERT INTO Orders (date, customer_id) VALUES (%s, %s)"
        cursor.execute(query, (order_data['date'], order_data['customer_id']))
        conn.commit()
        return jsonify({"message": "Order added successfully"}), 201

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# GET route for all orders
@app.route('/orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Orders")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders_schema.jsonify(orders)       

# UPDATE ORDER
@app.route("/orders/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    try:
        # validating json data throug the request
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": f"{err.messages}"}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database Connection Failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = "UPDATE Orders SET date = %s, customer_id = %s WHERE order_id = %s"
        date = order_data["date"]
        customer_id = order_data["customer_id"]
        updated_customer = (date, customer_id, order_id)
        cursor.execute(query, updated_customer)
        conn.commit()
        return jsonify({'message': "Order was updated successfully"}), 200
    
    except Error as e:
        return jsonify({"error": f"{e}"}), 500
    
    finally:
        cursor.close()
        conn.close()

# DELETE an Order
@app.route('/orders/<int:order_id>', methods=["DELETE"])
def delete_order(order_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        query = "DELETE FROM Orders WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        conn.commit()
        return jsonify({"message": "Order successfully deleted!"}), 200
    
    except Error as e:
        return jsonify({"error": f"{e}"}), 500
    
    finally:
        cursor.close()
        conn.close()
    


    










if __name__ == "__main__": #making sure only app.py can run the flask application    
    app.run(debug=True) #runs flask when we run the python file
    # and opens the debugger - robust information on errors within our application

