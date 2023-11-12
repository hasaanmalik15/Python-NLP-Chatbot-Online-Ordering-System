from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse 
import db_helpler 
import general_helper

app = FastAPI()

ongoing_order = {}

@app.post("/")
async def handle_request(request: Request):
    # get json data from request
    payload = await request.json()
    
    #extract required information from the payload based on structure of the webhookrequest from DialogFlow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = general_helper.extract_session_id(output_contexts[0]['name'])

    intent_dict = {
        'track.order - context:ongoing-order': track_order,
        'order.add-context:ongoing-order': add_to_order,
        'order.remove - context:ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order
    }

    return intent_dict[intent](parameters, session_id)


#creating track_order intent function 
def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['number'])
    order_status = db_helpler.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is {order_status}"
    else:
        fulfillment_text= f"No order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


#creating add_to_order intent function 
def add_to_order(parameters: dict, session_id: str):
    food_items = parameters["food-item"]
    quantity = parameters["number"]

    if len(food_items) != len(quantity):
        fulfillment_text = "Sorry I didn't catch that. Please specify food items and quantity for each food item clearly!"
    else:
        new_food_dict = dict(zip(food_items, quantity))
        if session_id in ongoing_order:
            current_food_dict = ongoing_order[session_id]
            current_food_dict.update(new_food_dict)
            ongoing_order[session_id] = current_food_dict
        else:
            ongoing_order[session_id] = new_food_dict
        
        # print("***********")
        # print(ongoing_order)

        order_str = general_helper.get_str_from_food_dict(ongoing_order[session_id])
        
        fulfillment_text = f"So far you have {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    }) 

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in ongoing_order:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    
    # food_items = parameters["food-item"]
    current_order = ongoing_order[session_id]
    food_items = parameters["food-item"].split(",")  # Split comma-separated items
    # food_items = [item.strip() for item in food_items]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = general_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })



# def remove_from_order(parameters: dict, session_id: str):
#     if session_id not in ongoing_order:
#         return JSONResponse(content={
#             "fulfillmentText": "Sorry! I am having trouble find your order. Can you please a new order?"
#         })
    
#     food_items = parameters["food-item"]
#     current_order = ongoing_order[session_id]
    
#     removed_items = []
#     no_such_items = []

#     for item in food_items:
#         if item not in current_order:
#             no_such_items.append(item)
#         else:
#             removed_items.append(item)
#             del current_order[item]

#     print("removed_items:", removed_items)
#     print("no_such_items:", no_such_items)
#     print("current_order:", current_order)

#     if len(removed_items) > 0:
#         # removed_items_str = ' '.join([str(items) for items in removed_items])
#         removed_items_str = ''.join(map(str, removed_items))
#         fulfillment_text = f'Removed {removed_items_str} from your order!'

#     if len(no_such_items) > 0:
#         # no_item_str = ' '.join([str(items) for items in no_such_items])
#         no_item_str = ''.join(map(str, no_such_items))
#         fulfillment_text = f'Your current order does not have {no_item_str}. '

#     if len(current_order.keys()) == 0:
#         fulfillment_text += "Your order is empty! "
#     else:
#         final_order = general_helper.get_str_from_food_dict(current_order)
#         fulfillment_text += f"Here is what is left in your order: {final_order}. Anything else? "
    
#     return JSONResponse(content={
#         "fulfillmentText": fulfillment_text
#     })

def complete_order(parameters: dict, session_id: str):
    if session_id not in ongoing_order:
        fulfillment_text = "Ooops. I am having trouble finding your order. Sorry! Can you please place a new order?"
    else:
        order = ongoing_order[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I couldnt place your order due to an error. " \
            "Please try placing a new order again"

        else:
            order_total = db_helpler.get_total_order_price(order_id)

            fulfillment_text = f"Awesome! I have placed your order." \
            f" Here is your order id # {order_id}." \
            f" Your total order amount is {order_total} and you can pay that at the time of your delivery!"
    
        del ongoing_order[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def save_to_db(order: dict):
    next_order_id = db_helpler.get_next_order_id()
    for food_item, quantity in order.items():
        rcode = db_helpler.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1
    

    db_helpler.insert_order_tracking(next_order_id, "In Progress")

    return next_order_id