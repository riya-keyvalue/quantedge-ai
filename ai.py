import json
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "sk-ALAdBLA8oDKq1s2sXS2Kpq85TZJER9Y_6lGEDkDM5wT3BlbkFJ3JCizfiR-FRRlMLnVKZY4yRvrCQe4yWQEPC2pKF3AA"

# Global variables to hold the conversation history and the JSON object
conversation_history = []
current_json = {}

user_prompt = """Strictly follow this json format:
{
        'message': '',
        'json_obj': {
          "strategy_name": null,
          "asset": {
          "symbol": null,
          "type": null,
            "expiry": {
                "cycle": null,
                "frequency": null
                }
          }
            "entry_trigger": {
                "type": null,
                "value": null
            },
            "contract_value": {
                "type": null,
                "value": null
            },
            "lot_size": null,
            "risk_management": {
                "stop_loss": {
                    "type": null,
                    "value": null
                },
                "take_profit": {
                    "type": null,
                    "value": null
                }
            },
            "exit_time": null,
            "actions": {
                "entry": null,
                "exit": null
            }
        }
        }
        And always return time in HHMM format without colon
        Exampe: 10:45 should be 1045
        Don't answer/suggest/recommend any strategies or talk about irrelevant things other than related to stock market or options or futures trading.
        Only answer the questions related to the stock market or options or futures trading.
        In case of irrelevant questions asked, return the message as 'IRRELEVANT TO THE CONTEXT' and return the same JSON object in 'json_obj'
        """


def chat_with_gpt(user_query):
    global conversation_history

    system_message = {
        "role": "system",
        "content": """You are an AI that converts textual options strategies into structured JSON. 
        Follow the below format when generating JSON.
        In case some values are not provided by the user, fill them with null.
        
        {
        'message': '',
        'json_obj': {
          "strategy_name": null,
          "asset": {
          "symbol": null,
          "type": null,
            "expiry": {
                "cycle": null,
                "frequency": null
                }
          }
            "entry_trigger": {
                "type": null,
                "value": null
            },
            "contract_value": {
                "type": null,
                "value": null
            },
            "lot_size": null,
            "risk_management": {
                "stop_loss": {
                    "type": null,
                    "value": null
                },
                "take_profit": {
                    "type": null,
                    "value": null
                }
            },
            "exit_time": null,
            "actions": {
                "entry": null,
                "exit": null
            }
        }
        }

        Follow the below constrains:
        - 'strategy_name' is just a strategy name that the user provides
        - 'asset_symbol' will only be one of (NIFTY, BANKNIFTY)
        - 'asset_symbol' is mandatory
        - 'asset_type' will be an array of strings containing either 'CE' or 'PE'
        - 'asset_type' is mandatory
        - 'asset_expiry_cycle will be one of (current, next)
        - 'asset_expiry_frequency' will be one of (weekly, monthly)
        - 'entry_trigger_type' will be time
        - 'entry_trigger_value' will be in HH:MM format
        - 'entry_trigger_type' is mandatory
        - 'entry_trigger_value' is mandatory
        - 'contract_value_type' will be one of (around, between, less, more)
        - 'contract_value_value' will be a float or an array of floats
        - 'contract_value_type' is mandatory
        - 'contract_value_value' is mandatory
        - 'lot_size' will be an integer
        - 'lot_size' is mandatory
        - 'risk_management_stop_loss_type' will be one of (percentage, value)
        - 'risk_management_stop_loss_value' will be an integer
        - 'risk_management_take_profit_type' will be one of (percentage, value)
        - 'risk_management_take_profit_value' will be an integer
        - 'risk_management' 'take_profit' is mandatory
        - 'risk_management' is not mandatory
        - 'risk_management_stop_loss_type', 'risk_management_stop_loss_value', 'risk_management_take_profit_type', 'risk_management_take_profit_value' are mandatory if 'risk_management' is present
        - 'exit_time' will be in HH:MM format
        - 'exit_time' is mandatory
        - 'actions_entry' will be one of (buy, sell)
        - 'actions_exit' will be one of (buy, sell)
        - 'actions_entry' is mandatory
        - take 'actions_exit' as the opposite of 'actions_entry' 
        

        
        Example 1:
        input: want to sell at 10 45 in ce and pe strikes around 2 rupees premium, keeping stoploss as 500% and target as 100%, universal exit at 3 15 pm, underlying asset is nifty
        
        Thought: Here, the 
        entry_trigger_value is '10:45', 
        asset_type is ['CE', 'PE'],
        contract_value_type is 'around', 
        contract_value_value is 2, 
        risk_management_stop_loss_type is 'percentage', 
        risk_management_stop_loss_value is 500, 
        risk_management_take_profit_type is 'percentage', 
        risk_management_take_profit_value is 100, 
        exit_time is '15:15', 
        actions_entry is 'sell', 
        so actions_exit will be 'buy',
        asset_symbol is 'NIFTY'
        asset_expiry_cycle is not mentioned, so it will be null
        asset_expiry_frequency is not mentioned, so it will be null
        lot_size is not mentioned, so it will be null

        So, the output JSON will be:
        {
        'message': 'Lets fill in the missing values. Please provide the lot size',
        'json_obj': {
          "strategy_name": OPTIONS BUYING STRATEGY,
          "asset": {
          "symbol": NIFTY,
          "type": ["CE", "PE"],
            "expiry": {
                "cycle": null,
                "frequency": null
                }
          }
            "entry_trigger": {
                "type": TIME,
                "value": 1045
            },
            "contract_value": {
                "type": AROUND,
                "value": 2
            },
            "lot_size": null,
            "risk_management": {
                "stop_loss": {
                    "type": PERCENTAGE,
                    "value": 500
                },
                "take_profit": {
                    "type": PERCENTAGE,
                    "value": 100
                }
            },
            "exit_time": 1515,
            "actions": {
                "entry": SELL,
                "exit": BUY
            }
        }
        }
        

        Example 2:
        input: want to buy at 10 45 in ce and pe strikes with premium less than 10, keeping stoploss 10 values and target as 10 values, universal exit at 3 00 pm, underlying asset is banknifty

        Thought: Here, the
        entry_trigger_value is '10:45',
        asset_type is ['CE', 'PE'],
        contract_value_type is 'less',
        contract_value_value is 10,
        risk_management_stop_loss_type is 'value',
        risk_management_stop_loss_value is 10,
        risk_management_take_profit_type is 'value',
        risk_management_take_profit_value is 10,
        exit_time is '15:00',
        actions_entry is 'buy',
        so actions_exit will be 'sell',
        asset_symbol is 'BANKNIFTY'
        asset_expiry_cycle is not mentioned, so it will be null
        asset_expiry_frequency is not mentioned, so it will be null
        lot_size is not mentioned, so it will be null

        So, the output JSON will be:
        {
        'message': 'Lets fill in the missing values. Please provide the strategy name',
        'json_obj': {
          "strategy_name": null,
          "asset": {
          "symbol": BANKNIFTY,
          "type": ["CE", "PE"],
            "expiry": {
                "cycle": null,
                "frequency": null
                }
          }
            "entry_trigger": {
                "type": TIME,
                "value": 1045
            },
            "contract_value": {
                "type": LESS,
                "value": 10
            },
            "lot_size": null,
            "risk_management": {
                "stop_loss": {
                    "type": VALUE,
                    "value": 10
                },
                "take_profit": {
                    "type": VALUE,
                    "value": 10
                }
            },
            "exit_time": 1500,
            "actions": {
                "entry": BUY,
                "exit": SELL
            }
        }
        }

        once you generate the json, ask for all the missing values one at a time and fill them in the json.

        Example 3:
        input: update my lot size to 30

        So, the output JSON will be:
        {
        'message': 'Your lot size is updated to 30',
        'json_obj': {
          "strategy_name": null,
          "asset": {
          "symbol": BANKNIFTY,
          "type": ["CE", "PE"],
            "expiry": {
                "cycle": null,
                "frequency": null
                }
          }
            "entry_trigger": {
                "type": TIME,
                "value": 1045
            },
            "contract_value": {
                "type": LESS,
                "value": 10
            },
            "lot_size": 30,
            "risk_management": {
                "stop_loss": {
                    "type": VALUE,
                    "value": 10
                },
                "take_profit": {
                    "type": VALUE,
                    "value": 10
                }
            },
            "exit_time": 1500,
            "actions": {
                "entry": BUY,
                "exit": SELL
            }
        }
        }

        Example 4:
        input: what is options

        So, the output JSON will be:
        {
        'message': 'Options are financial derivatives that provide investors with the right, but not the obligation, to buy or sell an underlying asset at a predetermined price, known as the strike price, before or on a specific expiration date. They are used for various purposes, including hedging, speculation, and enhancing portfolio returns. Here are some key concepts related to options',
        'json_obj': {
          "strategy_name": null,
          "asset": {
          "symbol": BANKNIFTY,
          "type": ["CE", "PE"],
            "expiry": {
                "cycle": null,
                "frequency": null
                }
          }
            "entry_trigger": {
                "type": TIME,
                "value": 1045
            },
            "contract_value": {
                "type": LESS,
                "value": 10
            },
            "lot_size": 30,
            "risk_management": {
                "stop_loss": {
                    "type": VALUE,
                    "value": 10
                },
                "take_profit": {
                    "type": VALUE,
                    "value": 10
                }
            },
            "exit_time": 1500,
            "actions": {
                "entry": BUY,
                "exit": SELL
            }
        }

        Stricty keep the json format intant, and once json is generated, ask for each and every missing values one at a time and fill them in the json.

    """,
    }

    conversation_history.append({"role": "system", "content": str(user_prompt)})
    conversation_history.append({"role": "user", "content": user_query})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[system_message] + conversation_history,
        max_tokens=1000,
        temperature=0.3,
    )

    response_content = response["choices"][0]["message"]["content"]
    response_content = response_content.replace("'", '"')
    # response_dict = json.loads(response_content)
    print("response_dict", response_content)
    conversation_history.append({"role": "assistant", "content": response_content})

    with open("strategy.json", "w") as json_file:
        json.dump(conversation_history, json_file, indent=4)

    return response_content  # Convert string response to dictionary


@app.route("/api/options", methods=["POST"])
def options():
    user_input = request.json.get("user_input", "")

    # Step 1: Generate initial JSON from user input
    global current_json

    # Step 2: Chat with GPT to modify or get information from the JSON
    gpt_response = chat_with_gpt(user_input)

    # Step 3: Return the response as JSON
    return gpt_response


if __name__ == "__main__":
    app.run(debug=True, port=5001)