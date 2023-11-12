import mysql.connector 
global cnx

cnx = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "root",
    database = "rodeo_food"
)

def get_order_status(order_id: int):
    try:
        #create cursor object
        cursor = cnx.cursor()

        #write executable sql query
        query = ("SELECT status FROM rodeo_food.order_tracking WHERE order_id = %s")

        #execute query
        cursor.execute(query, (order_id,))

        #fetch output
        result = cursor.fetchone()

     

        if result is not None:
            return result[0]
        else:
            return None
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        #connection close
        cursor.close()


def get_next_order_id():
    try:
        cursor = cnx.cursor()

        query = ("SELECT MAX(order_id) FROM rodeo_food.orders")

        cursor.execute(query)

        result = cursor.fetchone()[0]

        if result is None:
            return 1
        else:
            return result + 1

    except mysql.connector.Error as err:
        print(f"There was an error: {err}")
        return None
    
    finally:
        cursor.close()

def get_total_order_price(order_id: int):
    try:
        cursor = cnx.cursor()

        query = f"SELECT rodeo_food.get_total_order_price({order_id})"
        cursor.execute(query)
        
        result = cursor.fetchone()[0]

        return result

    except mysql.connector.Error as err:
        print(f"There was an error {err}")
        return None
    
    finally:
        cursor.close()


def insert_order_tracking(order_id, status):
    try:
        cursor = cnx.cursor()

        query = "INSERT INTO rodeo_food.order_tracking (order_id, status) VALUES (%s, %s)"
        cursor.execute(query, (order_id, status))
        cnx.commit()

    except mysql.connector.Error as err:
        print(f"Error {err}")
        return None
    finally:
        cursor.close()


def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        cnx.commit()

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        cnx.rollback()

        return -1 

    except Exception as e:
        print(f"An error has occurred: {e}")

        cnx.rollback()

        return -1
    
    finally:
        cursor.close()





    