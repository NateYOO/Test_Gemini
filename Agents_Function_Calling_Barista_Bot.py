{"cells":[{"cell_type":"markdown","metadata":{"id":"Tce3stUlHN0L"},"source":["##### Copyright 2024 Google LLC."]},{"cell_type":"code","execution_count":8,"metadata":{"id":"tuOe1ymfHZPu","executionInfo":{"status":"ok","timestamp":1719539676940,"user_tz":-540,"elapsed":371,"user":{"displayName":"YOUNGJIN YOO","userId":"15387966610067255142"}}},"outputs":[],"source":["# @title Licensed under the Apache License, Version 2.0 (the \"License\");\n","# you may not use this file except in compliance with the License.\n","# You may obtain a copy of the License at\n","#\n","# https://www.apache.org/licenses/LICENSE-2.0\n","#\n","# Unless required by applicable law or agreed to in writing, software\n","# distributed under the License is distributed on an \"AS IS\" BASIS,\n","# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n","# See the License for the specific language governing permissions and\n","# limitations under the License."]},{"cell_type":"markdown","metadata":{"id":"Ok-j-Bih_C5S"},"source":["# Gemini API: Agents and Automatic Function Calling with Barista Bot\n","\n","<table class=\"tfo-notebook-buttons\" align=\"left\">\n","  <td>\n","    <a target=\"_blank\" href=\"https://colab.research.google.com/github/google-gemini/cookbook/blob/main/examples/Agents_Function_Calling_Barista_Bot.ipynb\"><img src=\"https://www.tensorflow.org/images/colab_logo_32px.png\" />Run in Google Colab</a>\n","  </td>\n","</table>"]},{"cell_type":"markdown","metadata":{"id":"1YXoI96g_PLL"},"source":["This notebook shows a practical example of using automatic function calling with the Gemini API's Python SDK to build an agent. You will define some functions that comprise a café's ordering system, connect them to the Gemini API and write an agent loop that interacts with the user to order café drinks.\n","\n","The guide was inspired by the ReAct-style [Barista bot](https://aistudio.google.com/app/prompts/barista-bot) prompt available through AI Studio."]},{"cell_type":"code","execution_count":9,"metadata":{"id":"3IzLYKxmTHd5","executionInfo":{"status":"ok","timestamp":1719539688404,"user_tz":-540,"elapsed":7018,"user":{"displayName":"YOUNGJIN YOO","userId":"15387966610067255142"}}},"outputs":[],"source":["!pip install -qU google-generativeai"]},{"cell_type":"markdown","metadata":{"id":"zFjRBXVrAdYB"},"source":["To run this notebook, your API key must be stored it in a Colab Secret named `GOOGLE_API_KEY`. If you are running in a different environment, you can store your key in an environment variable. See [Authentication](../quickstarts/Authentication.ipynb) to learn more."]},{"cell_type":"code","source":["import os\n","from dotenv import load_dotenv\n","import google.generativeai as genai\n","\n","# .env 파일에서 환경 변수 로드\n","load_dotenv()\n","\n","# 환경 변수에서 API 키 가져오기\n","api_key = os.getenv(\"AIzaSyAbHQK9OtDTG5x5P1L_9YCnj7DwwoKf88w\")\n","\n","# API 키 설정\n","genai.configure(api_key=api_key)"],"metadata":{"colab":{"base_uri":"https://localhost:8080/","height":394},"id":"0DPc41uXjY8S","executionInfo":{"status":"error","timestamp":1719539724176,"user_tz":-540,"elapsed":515,"user":{"displayName":"YOUNGJIN YOO","userId":"15387966610067255142"}},"outputId":"2a10dd24-a1b0-4438-c073-9eb66c938429"},"execution_count":10,"outputs":[{"output_type":"error","ename":"ModuleNotFoundError","evalue":"No module named 'dotenv'","traceback":["\u001b[0;31m---------------------------------------------------------------------------\u001b[0m","\u001b[0;31mModuleNotFoundError\u001b[0m                       Traceback (most recent call last)","\u001b[0;32m<ipython-input-10-24cdd52e52c0>\u001b[0m in \u001b[0;36m<cell line: 2>\u001b[0;34m()\u001b[0m\n\u001b[1;32m      1\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mos\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0;32m----> 2\u001b[0;31m \u001b[0;32mfrom\u001b[0m \u001b[0mdotenv\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mload_dotenv\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0m\u001b[1;32m      3\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mgoogle\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mgenerativeai\u001b[0m \u001b[0;32mas\u001b[0m \u001b[0mgenai\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      4\u001b[0m \u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      5\u001b[0m \u001b[0;31m# .env 파일에서 환경 변수 로드\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n","\u001b[0;31mModuleNotFoundError\u001b[0m: No module named 'dotenv'","","\u001b[0;31m---------------------------------------------------------------------------\u001b[0;32m\nNOTE: If your import is failing due to a missing package, you can\nmanually install dependencies using either !pip or !apt.\n\nTo view examples of installing some common dependencies, click the\n\"Open Examples\" button below.\n\u001b[0;31m---------------------------------------------------------------------------\u001b[0m\n"],"errorDetails":{"actions":[{"action":"open_url","actionText":"Open Examples","url":"/notebooks/snippets/importing_libraries.ipynb"}]}}]},{"cell_type":"code","execution_count":12,"metadata":{"id":"0gOuwcCUTNAO","colab":{"base_uri":"https://localhost:8080/","height":305},"executionInfo":{"status":"error","timestamp":1719539752307,"user_tz":-540,"elapsed":2059,"user":{"displayName":"YOUNGJIN YOO","userId":"15387966610067255142"}},"outputId":"2593f9ba-073e-4eb3-c0a2-bb6f55aa5757"},"outputs":[{"output_type":"error","ename":"SecretNotFoundError","evalue":"Secret AIzaSyAbHQK9OtDTG5x5P1L_9YCnj7DwwoKf88w does not exist.","traceback":["\u001b[0;31m---------------------------------------------------------------------------\u001b[0m","\u001b[0;31mSecretNotFoundError\u001b[0m                       Traceback (most recent call last)","\u001b[0;32m<ipython-input-12-002df39c4a66>\u001b[0m in \u001b[0;36m<cell line: 8>\u001b[0;34m()\u001b[0m\n\u001b[1;32m      6\u001b[0m \u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      7\u001b[0m \u001b[0;32mfrom\u001b[0m \u001b[0mgoogle\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mcolab\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0muserdata\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0;32m----> 8\u001b[0;31m \u001b[0mgenai\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mconfigure\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0mapi_key\u001b[0m\u001b[0;34m=\u001b[0m\u001b[0muserdata\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mget\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0;34m\"AIzaSyAbHQK9OtDTG5x5P1L_9YCnj7DwwoKf88w\"\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0m","\u001b[0;32m/usr/local/lib/python3.10/dist-packages/google/colab/userdata.py\u001b[0m in \u001b[0;36mget\u001b[0;34m(key)\u001b[0m\n\u001b[1;32m     51\u001b[0m     )\n\u001b[1;32m     52\u001b[0m   \u001b[0;32mif\u001b[0m \u001b[0;32mnot\u001b[0m \u001b[0mresp\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mget\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0;34m'exists'\u001b[0m\u001b[0;34m,\u001b[0m \u001b[0;32mFalse\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m:\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0;32m---> 53\u001b[0;31m     \u001b[0;32mraise\u001b[0m \u001b[0mSecretNotFoundError\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0mkey\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0m\u001b[1;32m     54\u001b[0m   \u001b[0;32mif\u001b[0m \u001b[0;32mnot\u001b[0m \u001b[0mresp\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mget\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0;34m'access'\u001b[0m\u001b[0;34m,\u001b[0m \u001b[0;32mFalse\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m:\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m     55\u001b[0m     \u001b[0;32mraise\u001b[0m \u001b[0mNotebookAccessError\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0mkey\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n","\u001b[0;31mSecretNotFoundError\u001b[0m: Secret AIzaSyAbHQK9OtDTG5x5P1L_9YCnj7DwwoKf88w does not exist."]}],"source":["from random import randint\n","from typing import Iterable\n","\n","import google.generativeai as genai\n","from google.api_core import retry\n","\n","from google.colab import userdata\n","genai.configure(api_key=userdata.get(\"AIzaSyAbHQK9OtDTG5x5P1L_9YCnj7DwwoKf88w\"))"]},{"cell_type":"markdown","metadata":{"id":"F72jp1hzA8zU"},"source":["## Define the API\n","\n","To emulate a café's ordering system, define functions for managing the customer's order: adding, editing, clearing, confirming and fulfilling.\n","\n","These functions track the customer's order using the global variables `order` (the in-progress order) and `placed_order` (the confirmed order sent to the kitchen). Each of the order-editing functions updates the `order`, and once placed, `order` is copied to `placed_order` and cleared.\n","\n","In the Python SDK you can pass functions directly to the model constructor, where the SDK will inspect the type signatures and docstrings to define the `tools`. For this reason it's important that you correctly type each of the parameters, give the functions sensible names and detailed docstrings."]},{"cell_type":"code","execution_count":null,"metadata":{"id":"wMltPyUpTu3h"},"outputs":[],"source":["order = []  # The in-progress order.\n","placed_order = []  # The confirmed, completed order.\n","\n","def add_to_order(drink: str, modifiers: Iterable[str] = ()) -> None:\n","  \"\"\"Adds the specified drink to the customer's order, including any modifiers.\"\"\"\n","  order.append((drink, modifiers))\n","\n","\n","def get_order() -> Iterable[tuple[str, Iterable[str]]]:\n","  \"\"\"Returns the customer's order.\"\"\"\n","  return order\n","\n","\n","def remove_item(n: int) -> str:\n","  \"\"\"Remove the nth (one-based) item from the order.\n","\n","  Returns:\n","    The item that was removed.\n","  \"\"\"\n","  item, modifiers = order.pop(int(n) - 1)\n","  return item\n","\n","\n","def clear_order() -> None:\n","  \"\"\"Removes all items from the customer's order.\"\"\"\n","  order.clear()\n","\n","\n","def confirm_order() -> str:\n","  \"\"\"Asks the customer if the order is correct.\n","\n","  Returns:\n","    The user's free-text response.\n","  \"\"\"\n","\n","  print('Your order:')\n","  if not order:\n","    print('  (no items)')\n","\n","  for drink, modifiers in order:\n","    print(f'  {drink}')\n","    if modifiers:\n","      print(f'   - {\", \".join(modifiers)}')\n","\n","  return input('Is this correct? ')\n","\n","\n","def place_order() -> int:\n","  \"\"\"Submit the order to the kitchen.\n","\n","  Returns:\n","    The estimated number of minutes until the order is ready.\n","  \"\"\"\n","  placed_order[:] = order.copy()\n","  clear_order()\n","\n","  # TODO(you!): Implement coffee fulfilment.\n","  return randint(1, 10)"]},{"cell_type":"markdown","metadata":{"id":"e7l3_vBtC0oF"},"source":["## Test the API\n","\n","With the functions written, test that they work as expected."]},{"cell_type":"code","execution_count":null,"metadata":{"id":"jg1LjYNUWnsC","outputId":"71c55059-78ce-4b61-93d8-e517ec756f47"},"outputs":[{"name":"stdout","output_type":"stream","text":["Your order:\n","  Latte\n","   - Extra shot\n","  Tea\n","   - Earl Grey, hot\n"]},{"name":"stdin","output_type":"stream","text":["Is this correct?  yes\n"]}],"source":["# Test it out!\n","\n","clear_order()\n","add_to_order('Latte', ['Extra shot'])\n","add_to_order('Tea')\n","remove_item(2)\n","add_to_order('Tea', ['Earl Grey', 'hot'])\n","confirm_order();"]},{"cell_type":"markdown","metadata":{"id":"gOhiADoCC811"},"source":["## Define the prompt\n","\n","Here you define the full Barista-bot prompt. This prompt contains the café's menu items and modifiers and some instructions.\n","\n","The instructions include guidance on how functions should be called (e.g. \"Always `confirm_order` with the user before calling `place_order`\"). You can modify this to add your own interaction style to the bot, for example if you wanted to have the bot repeat every request back before adding to the order, you could provide that instruction here.\n","\n","The end of the prompt includes some jargon the bot might encounter, and instructions _du jour_ - in this case it notes that the café has run out of soy milk."]},{"cell_type":"code","execution_count":null,"metadata":{"id":"IoBvZ1JYXgn5"},"outputs":[],"source":["COFFEE_BOT_PROMPT = \"\"\"\\You are a coffee order taking system and you are restricted to talk only about drinks on the MENU. Do not talk about anything but ordering MENU drinks for the customer, ever.\n","Your goal is to do place_order after understanding the menu items and any modifiers the customer wants.\n","Add items to the customer's order with add_to_order, remove specific items with remove_item, and reset the order with clear_order.\n","To see the contents of the order so far, call get_order (by default this is shown to you, not the user)\n","Always confirm_order with the user (double-check) before calling place_order. Calling confirm_order will display the order items to the user and returns their response to seeing the list. Their response may contain modifications.\n","Always verify and respond with drink and modifier names from the MENU before adding them to the order.\n","If you are unsure a drink or modifier matches those on the MENU, ask a question to clarify or redirect.\n","You only have the modifiers listed on the menu below: Milk options, espresso shots, caffeine, sweeteners, special requests.\n","Once the customer has finished ordering items, confirm_order and then place_order.\n","\n","Hours: Tues, Wed, Thurs, 10am to 2pm\n","Prices: All drinks are free.\n","\n","MENU:\n","Coffee Drinks:\n","Espresso\n","Americano\n","Cold Brew\n","\n","Coffee Drinks with Milk:\n","Latte\n","Cappuccino\n","Cortado\n","Macchiato\n","Mocha\n","Flat White\n","\n","Tea Drinks:\n","English Breakfast Tea\n","Green Tea\n","Earl Grey\n","\n","Tea Drinks with Milk:\n","Chai Latte\n","Matcha Latte\n","London Fog\n","\n","Other Drinks:\n","Steamer\n","Hot Chocolate\n","\n","Modifiers:\n","Milk options: Whole, 2%, Oat, Almond, 2% Lactose Free; Default option: whole\n","Espresso shots: Single, Double, Triple, Quadruple; default: Double\n","Caffeine: Decaf, Regular; default: Regular\n","Hot-Iced: Hot, Iced; Default: Hot\n","Sweeteners (option to add one or more): vanilla sweetener, hazelnut sweetener, caramel sauce, chocolate sauce, sugar free vanilla sweetener\n","Special requests: any reasonable modification that does not involve items not on the menu, for example: 'extra hot', 'one pump', 'half caff', 'extra foam', etc.\n","\n","\"dirty\" means add a shot of espresso to a drink that doesn't usually have it, like \"Dirty Chai Latte\".\n","\"Regular milk\" is the same as 'whole milk'.\n","\"Sweetened\" means add some regular sugar, not a sweetener.\n","\n","Soy milk has run out of stock today, so soy is not available.\n","\"\"\""]},{"cell_type":"markdown","metadata":{"id":"c_ybYQ-sU7rn"},"source":["## Set up the model\n","\n","In this step you collate the functions into a \"system\" that is passed as `tools`, instantiate the model and start the chat session.\n","\n","This block includes two options for interacting with the Gemini API. By toggling `use_sys_inst`, you can switch between using Gemini 1.5 Pro with a system instruction (highest quality but free-tier quota may be insufficient for a long chat session) or Gemini 1.0 Pro (higher free quota but does not support system instructions).\n","\n","A retriable `send_message` function is also defined to help with low-quota conversations."]},{"cell_type":"code","execution_count":null,"metadata":{"id":"8vmtzAlPaQH-"},"outputs":[],"source":["ordering_system = [add_to_order, get_order, remove_item, clear_order, confirm_order, place_order]\n","\n","# Toggle this to switch between Gemini 1.5 with a system instruction, or Gemini 1.0 Pro.\n","use_sys_inst = False\n","\n","model_name = 'gemini-1.5-flash' if use_sys_inst else 'gemini-1.0-pro'\n","\n","if use_sys_inst:\n","  model = genai.GenerativeModel(\n","      model_name, tools=ordering_system, system_instruction=COFFEE_BOT_PROMPT)\n","  convo = model.start_chat(enable_automatic_function_calling=True)\n","\n","else:\n","  model = genai.GenerativeModel(model_name, tools=ordering_system)\n","  convo = model.start_chat(\n","      history=[\n","          {'role': 'user', 'parts': [COFFEE_BOT_PROMPT]},\n","          {'role': 'model', 'parts': ['OK I understand. I will do my best!']}\n","        ],\n","      enable_automatic_function_calling=True)\n","\n","\n","@retry.Retry(initial=30)\n","def send_message(message):\n","  return convo.send_message(message)\n","\n","\n","placed_order = []\n","order = []"]},{"cell_type":"markdown","metadata":{"id":"624ai2Q5WMAF"},"source":["## Chat with Barista Bot\n","\n","With the model defined and chat created, all that's left is to connect the user input to the model and display the output, in a loop. This loop continues until an order is placed.\n","\n","When run in Colab, any fixed-width text originates from your Python code (e.g. `print` calls in the ordering system), regular text comes the Gemini API, and the outlined boxes allow for user input that is rendered with a leading `>`.\n","\n","Try it out!"]},{"cell_type":"code","execution_count":null,"metadata":{"id":"38SAyrNNVhvE","outputId":"25f61547-b2cb-4579-cd91-e8ac29af3bf6"},"outputs":[{"name":"stdout","output_type":"stream","text":["Welcome to Barista bot!\n","\n","\n"]},{"name":"stdin","output_type":"stream","text":[">  I would like a capuccino with almond milk\n"]},{"data":{"text/markdown":["I have added a Cappuccino with Almond Milk to your order."],"text/plain":["<IPython.core.display.Markdown object>"]},"metadata":{},"output_type":"display_data"},{"name":"stdin","output_type":"stream","text":[">  do you have stone milk?\n"]},{"data":{"text/markdown":["I'm sorry, we do not have Stone Milk on the menu. Would you like any other type of milk with your cappuccino?"],"text/plain":["<IPython.core.display.Markdown object>"]},"metadata":{},"output_type":"display_data"},{"name":"stdin","output_type":"stream","text":[">  no, that's all\n"]},{"name":"stdout","output_type":"stream","text":["Your order:\n","  Cappuccino\n","   - Almond Milk\n"]},{"name":"stdin","output_type":"stream","text":["Is this correct?  yes\n"]},{"data":{"text/markdown":["Ok, I will place the order now."],"text/plain":["<IPython.core.display.Markdown object>"]},"metadata":{},"output_type":"display_data"},{"name":"stdin","output_type":"stream","text":[">  thanks\n"]},{"data":{"text/markdown":["Your order will be ready in about 10 minutes."],"text/plain":["<IPython.core.display.Markdown object>"]},"metadata":{},"output_type":"display_data"},{"name":"stdout","output_type":"stream","text":["\n","\n","\n","[barista bot session over]\n","\n","Your order:\n","  [('Cappuccino', ['Almond Milk'])]\n","\n","- Thanks for using Barista Bot!\n"]}],"source":["from IPython.display import display, Markdown\n","\n","print('Welcome to Barista bot!\\n\\n')\n","\n","while not placed_order:\n","  response = send_message(input('> '))\n","  display(Markdown(response.text))\n","\n","\n","print('\\n\\n')\n","print('[barista bot session over]')\n","print()\n","print('Your order:')\n","print(f'  {placed_order}\\n')\n","print('- Thanks for using Barista Bot!')"]},{"cell_type":"markdown","metadata":{"id":"lr0xv8BIdXCQ"},"source":["Some things to try:\n","* Ask about the menu (e.g. \"what coffee drinks are available?\")\n","* Use terms that are not specified in the prompt (e.g. \"a strong latte\" or \"an EB tea\")\n","* Change your mind part way through (\"uhh cancel the latte sorry\")\n","* Go off-menu (\"a babycino\")"]},{"cell_type":"markdown","metadata":{"id":"W438QHRGbLcB"},"source":["## See also\n","\n","This sample app showed you how to integrate a traditional software system (the coffee ordering functions) and an AI agent powered by the Gemini API. This is a simple, practical way to use LLMs that allows for open-ended human language input and output that feels natural, but still keeps a human in the loop to ensure correct operation.\n","\n","To learn more about how Barista Bot works, check out:\n","\n","* The [Barista Bot](https://aistudio.google.com/app/prompts/barista-bot) prompt\n","* [System instructions](../quickstarts/System_instructions.ipynb)\n","* [Automatic function calling](../quickstarts/Function_calling.ipynb)\n"]}],"metadata":{"colab":{"toc_visible":true,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"}},"nbformat":4,"nbformat_minor":0}