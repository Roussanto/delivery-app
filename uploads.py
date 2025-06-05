from datetime import datetime

import _tkinter
import mysql.connector
from tkinter import messagebox
from colorama import Fore

from func import check_none_type, workday_exists, address_exists, customer_exists, make_columns_str, create_relations


# This function connects to the mysql database and returns the database itself.
# The database is used as an input to upload into it data
def connect_database():
    # Connect to database
    income_db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Roussanto171!"
    )

    # Create cursor object
    cursor = income_db.cursor()

    # Use database
    cursor.execute("USE income;")

    return income_db


def upload_workday(database, dict_var):
    # Create cursor object
    cursor = database.cursor()

    # Export the variables' input
    date = datetime.strptime(dict_var["date"].get(), "%Y-%m-%d").date()
    hours = dict_var["hours"].get()
    payment = dict_var["payment"].get()

    if workday_exists(database, date):
        print(Fore.BLUE + "Workday already exists!")
    else:
        # Insert workday data query
        query = ("INSERT INTO workdays (date, hours, payment) "
                 f"VALUES (%s, %s, %s);")

        # Execute query and save changes
        cursor.execute(query, (date, hours, payment))
        database.commit()

        print(Fore.GREEN + "Workday upload successful!")


def upload_address(database, dict_var):
    # Create cursor object
    cursor = database.cursor()

    # Export the variables' input
    address = dict_var["address"].get()
    latitude = dict_var["latitude"].get()
    longitude = dict_var["longitude"].get()

    # check_none_type returns (val,) because it's only one value in tuple.
    # To extract the val itself we use val[0]
    address = check_none_type(address)[0]

    # If the address already exists then a warning appears notifying us
    # If not, then the new address is added into the database
    if address_exists(database, address):
        print(Fore.BLUE + "Address already exists!")
    else:
        # Insert address data query
        query = ("INSERT INTO addresses (name, latitude, longitude) "
                 f"VALUES (%s, %s, %s);")

        # Execute query and save changes
        cursor.execute(query, (address, latitude, longitude))
        database.commit()

        print(Fore.GREEN + "Address upload successful!")


def upload_customer(database, dict_var, address_name):
    # Create cursor object
    cursor = database.cursor()

    # Export the variables' input
    customer_name = dict_var["customer name"].get()
    floor = dict_var["floor"].get()

    # Empty customer, floor entries means that the input is a string of length 0.
    # We need to make it NoneType, so the db can decline the input of an empty input.
    customer_name, floor = check_none_type(customer_name, floor)

    # If the customer name already exists and is already associated with the inputted address,
    # then the customer already exists in the database
    # Else,they have to be inserted into the database.
    if customer_exists(database, address_name, customer_name):
        print(Fore.BLUE + "Customer already exists!")
    else:
        # Insert customer data. address_id is the inputted address's id.
        query = ("INSERT INTO customers (name, address_id, floor) "
                 "SELECT %s, id, %s "
                 f"FROM addresses WHERE name = '{address_name}';")

        # Execute query and save changes
        cursor.execute(query, (customer_name, floor))
        database.commit()

        print(Fore.GREEN + "Customer upload successful!")


def upload_order(database, dict_var, workday_date, customer_name, address_name):
    # Create cursor object
    cursor = database.cursor()

    # Export the variables' input
    order_time = datetime.strptime(dict_var["order time"].get(), "%H:%M:%S").time()
    delivery_time = datetime.strptime(dict_var["delivery time"].get(), "%H:%M:%S").time()
    tips = dict_var["tips"].get()
    tips_method = dict_var["tips method"].get()
    source = dict_var["source"].get()
    payment_method = dict_var["payment method"].get()

    # Empty entries means that the input is a string of length 0.
    # We need to make it NoneType, so the db can decline the input of an empty input.
    order_time, delivery_time, tips, tips_method, source, payment_method = check_none_type(order_time,
                                                                                                 delivery_time,
                                                                                                 tips,
                                                                                                 tips_method,
                                                                                                 source,
                                                                                                 payment_method)

    # If no tips have been added, make them 0
    if tips == "":
        tips = 0.0

    # Insert order data query
    # First detect the current workday's id
    cursor.execute(f"SELECT id FROM workdays WHERE date = '{workday_date}';")
    workday_id = cursor.fetchall()[0][0]

    query = ("INSERT INTO orders (customer_id, workday_id, order_time, delivery_time, tips, tips_method, source, payment_method) "
             "SELECT id, %s, %s, %s, %s, %s, %s, %s FROM customers "
             f"WHERE name = '{customer_name}' "
             "AND address_id = ("
             "                  SELECT id FROM addresses"
             f"                 WHERE name = '{address_name}'"
             ");")

    # Execute query and save changes
    cursor.execute(query, (workday_id, order_time, delivery_time, tips, tips_method, source, payment_method))
    database.commit()

    print(Fore.GREEN + "Order upload successful!")


def upload_items(database, basket, customer_dict, address_dict, workday_dict, order_dict):
    # Create cursor object
    cursor = database.cursor()

    # Export the variables' input
    for item in basket:
        # Make empty StringVars to None
        for key in list(item.keys()):
            item[key] = check_none_type(item[key])[0]

        if item["category"] == "Coffee":
            db_tablename = "coffees"
        elif item["category"] == "Freddo or Flat":
            db_tablename = "freddos_flats"
        elif item["category"] == "Filter":
            db_tablename = "filters"
        elif item["category"] == "Chocolate":
            db_tablename = "chocolates"
        elif item["category"] == "Food":
            db_tablename = "foods"
        elif item["category"] == "Beverage":
            db_tablename = "beverages"
        elif item["category"] == "Chamomile":
            db_tablename = "chamomiles"
        elif item["category"] == "Weird Chocolate":
            db_tablename = "weird_chocolates"
        elif item["category"] == "Tee":
            db_tablename = "tees"
        elif item["category"] == "Smoothie":
            db_tablename = "smoothies"

        # columns: (column 1, ..., column n)
        # values (%s, ..., %s)
        columns, values_num = make_columns_str(item)
        # inserts: a tuple form of the items
        inserts = tuple([val for key, val in list(item.items()) if key not in ["offer", "category"]])

        # Insert address data query
        query = (f"INSERT INTO {db_tablename} {columns} "
                 f"VALUES {values_num};")

        # Execute query and save changes
        cursor.execute(query, inserts)

        create_relations(cursor, item, customer_dict, address_dict, workday_dict, order_dict, db_tablename)

        database.commit()

    print(Fore.GREEN + "Items upload successful!")
    print()


def upload_data(workday_tab, addr_cust_tab, order_tab, basket):
    # Connect to the database
    database = connect_database()

    # Flags
    workday_success = False
    address_success = False
    customer_success = False

    # Upload inputs from gui.
    # The following functions also check if the address or the customer already exist in the database
    # Upload workday
    try:
        workday_dict = workday_tab.workday_frame.workday_dict

        if workday_dict["date"].get() and workday_dict["hours"].get() and workday_dict["payment"].get() > 0.0:
            upload_workday(database, workday_dict)
            workday_success = True
        else:
            messagebox.showerror("Error", "You have not inserted your workday.")
    except _tkinter.TclError:
        messagebox.showerror("Error", "You have not inserted your workday.")

    # Upload address
    address_dict = addr_cust_tab.address_frame.address_dict

    if workday_success:
        if address_dict["address"].get():
            upload_address(database, address_dict)
            address_success = True
        else:
            messagebox.showerror("Error", "You have not inserted a customer's address.")

    # Upload customer
    customer_dict = addr_cust_tab.customer_frame.customer_dict
    address = addr_cust_tab.address_frame.address_var.get()

    if workday_success and address_success:
        if customer_dict["customer name"].get():
            upload_customer(database, customer_dict, address)
            customer_success = True
        else:
            messagebox.showerror("Error", "You have not inserted a customer.")

    # Upload order
    order_dict = order_tab.order_frame.order_dict
    order_date = workday_tab.workday_frame.date_var.get()
    customer_name = addr_cust_tab.customer_frame.customer_var.get()

    if workday_success and address_success and customer_success:
        if order_dict["order time"].get() and order_dict["delivery time"] and order_dict["source"].get() and order_dict["payment method"].get():
            upload_order(database, order_dict, order_date, customer_name, address)
        else:
            messagebox.showerror("Error", "You have not inserted an order.")

    # Upload item
    upload_items(database, basket, customer_dict, address_dict, workday_dict, order_dict)
