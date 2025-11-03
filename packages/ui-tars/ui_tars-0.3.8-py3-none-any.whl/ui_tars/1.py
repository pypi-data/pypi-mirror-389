# # pip install --upgrade ui-tars
# from ui_tars.action_parser import parse_xml_action_v3

# response = """<gui_think>好的，现在文档内容已经全部选中了。我注意到工具栏上有个背景颜色的按钮，旁边有个小箭头，点击它就能打开颜色选择面板。我需要在里面选择"无填充"选项，这样就能一次性清除所有文字的黄色高亮了。</gui_think>
# <seed:tool_call_never_used_51bce0c785ca2f68081bfa7d91973934>
# <function_never_used_51bce0c785ca2f68081bfa7d91973934=click>
# <parameter_never_used_51bce0c785ca2f68081bfa7d91973934=point><object><parameter_never_used_51bce0c785ca2f68081bfa7d91973934=x>539</parameter_never_used_51bce0c785ca2f68081bfa7d91973934><parameter_never_used_51bce0c785ca2f68081bfa7d91973934=y>130</parameter_never_used_51bce0c785ca2f68081bfa7d91973934></object></parameter_never_used_51bce0c785ca2f68081bfa7d91973934>
# </function_never_used_51bce0c785ca2f68081bfa7d91973934>
# </seed:tool_call_never_used_51bce0c785ca2f68081bfa7d91973934>""" # 模型原始输出

# tool_schemas = [
#         {
#             "type": "function",
#             "name": "click",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "point": {
#                         "type": "object",
#                         "properties": {
#                             "x": {
#                                 "type": "integer",
#                                 "description": "Click coordinates. The format is: <point>x y</point>"
#                             },
#                             "y": {
#                                 "type": "integer",
#                                 "description": "Click coordinates. The format is: <point>x y</point>"
#                             },
#                             "z": {
#                                 "type": "integer",
#                                 "description": "Click coordinates. The format is: <point>x y</point>"
#                             }
#                         },
#                         "required": [
#                             "x",
#                             "y"
#                         ]
#                     }
#                 },
                
#             },
#             "description": "Mouse left single click action."
#         }
#     ]

# think_end_token = "</gui_think>" # 根据具体场景定，用于抽取final answer，某些场景模型finish时会以这种形式：<think_start_token> thinking_process <think_end_token> finish_content

# parsed_responses = parse_xml_action_v3(
#     response,
#     tool_schemas
# )

# print("Parsed responses: ", parsed_responses)


# pip install ui-tars==0.3.4
from ui_tars.action_parser import parse_xml_action_v2, parsing_response_to_pyautogui_code
import base64
import io
import requests
from PIL import Image

# tool schemas
tool_schemas = [
    {
        "type": "function",
        "name": "open_computer",
        "parameters": {},
        "description": "Open computer."
    },
    {
        "type": "function",
        "name": "click",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Click coordinates. The format is: <point>x y</point>"
                }
            },
            "required": [
                "point"
            ]
        },
        "description": "Mouse left single click action."
    },
    {
        "type": "function",
        "name": "left_double",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Click coordinates. The format is: <point>x y</point>"
                }
            },
            "required": [
                "point"
            ]
        },
        "description": "Mouse left double click action."
    },
    {
        "type": "function",
        "name": "right_single",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Click coordinates. The format is: <point>x y</point>"
                }
            },
            "required": [
                "point"
            ]
        },
        "description": "Mouse right single click action."
    },
    {
        "type": "function",
        "name": "scroll",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Scroll start position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>"
                },
                "direction": {
                    "type": "string",
                    "description": "Scroll direction.",
                    "enum": [
                        "up",
                        "down",
                        "left",
                        "right"
                    ]
                }
            },
            "required": [
                "direction"
            ]
        },
        "description": "Scroll action."
    },
    {
        "type": "function",
        "name": "move_to",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Target coordinates. The format is: <point>x y</point>"
                }
            },
            "required": [
                "point"
            ]
        },
        "description": "Mouse move action."
    },
    {
        "type": "function",
        "name": "hotkey",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Hotkeys you want to press. Split keys with a space and use lowercase."
                }
            },
            "required": [
                "key"
            ]
        },
        "description": "Press hotkey."
    },
    {
        "type": "function",
        "name": "finished",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Provide the final answer or response to complete the task."
                }
            },
            "required": []
        },
        "description": "This function is used to indicate the completion of a task by providing the final answer or response."
    },
    {
        "type": "function",
        "name": "press",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Key you want to press. Only one key can be pressed at one time."
                }
            },
            "required": [
                "key"
            ]
        },
        "description": "Press key."
    },
    {
        "type": "function",
        "name": "release",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Key you want to release. Only one key can be released at one time."
                }
            },
            "required": [
                "key"
            ]
        },
        "description": "Release key."
    },
    {
        "type": "function",
        "name": "mouse_down",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Mouse down position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>"
                },
                "button": {
                    "type": "string",
                    "description": "Down button. Default to left.",
                    "enum": [
                        "left",
                        "right"
                    ]
                }
            },
            "required": []
        },
        "description": "Mouse down action."
    },
    {
        "type": "function",
        "name": "mouse_up",
        "parameters": {
            "type": "object",
            "properties": {
                "point": {
                    "type": "string",
                    "description": "Mouse up position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>"
                },
                "button": {
                    "type": "string",
                    "description": "Up button. Default to left.",
                    "enum": [
                        "left",
                        "right"
                    ]
                }
            },
            "required": []
        },
        "description": "Mouse up action."
    },
    {
        "type": "function",
        "name": "call_user",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Message or information displayed to the user to request their input, feedback, or guidance."
                }
            },
            "required": []
        },
        "description": "This function is used to interact with the user by displaying a message and requesting their input, feedback, or guidance."
    },
    {
        "type": "function",
        "name": "wait",
        "parameters": {
            "type": "object",
            "properties": {
                "time": {
                    "type": "integer",
                    "description": "Wait time in seconds."
                }
            },
            "required": []
        },
        "description": "Wait for a while."
    },
    {
        "type": "function",
        "name": "drag",
        "parameters": {
            "type": "object",
            "properties": {
                "start_point": {
                    "type": "string",
                    "description": "Drag start point. The format is: <point>x y</point>"
                },
                "end_point": {
                    "type": "string",
                    "description": "Drag end point. The format is: <point>x y</point>"
                }
            },
            "required": [
                "start_point",
                "end_point"
            ]
        },
        "description": "Mouse left button drag action."
    },
    {
        "type": "function",
        "name": "type",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Type content. If you want to submit your input, use \n at the end of content."
                }
            },
            "required": [
                "content"
            ]
        },
        "description": "Type content."
    },
    {
        "type": "function",
        "name": "open_computer",
        "parameters": {},
        "description": "Open computer."
    },
    {
        "type": "function",
        "name": "take_screenshot",
        "parameters": {},
        "description": "Take screenshot."
    }
]


# inputs prepare

def pil_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str


def inference(messages):

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        # "max_tokens": 400,
        "top_p": 0.9,
        # "temperature": self.temperature,
        "temperature": 0.0,
    }
    
    response = requests.post(base_url, headers=headers, json=data)
    try:
        print(f"Response: {response.json()}")
    except:
        print("Error fetching response.json:")
        print(response)
        
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.json())
        return {
            "error": f"Request failed with status code {response.status_code}",
            "details": response.text
        }
        
api_key = "efa2ecef-c5eb-44e1-8853-86c592d7cdc2"
base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
model = "ep-20250926152455-74xj7"
image = Image.open("test.png")
base64_image = pil_to_base64(image)



messages = [
    {
        "role": "system",
        "content": "You should begin by detailing the internal reasoning process, and then present the answer to the user. The reasoning process should be enclosed within <think_never_used_51bce0c785ca2f68081bfa7d91973934> </think_never_used_51bce0c785ca2f68081bfa7d91973934> tags, as follows:\n<think_never_used_51bce0c785ca2f68081bfa7d91973934> reasoning process here </think_never_used_51bce0c785ca2f68081bfa7d91973934> answer here. \n\nYou have different modes of thinking:\nUnrestricted think mode: Engage in an internal thinking process with thorough reasoning and reflections. You have an unlimited budget for thinking tokens and can continue thinking until you fully solve the problem.\nEfficient think mode: Provide a concise internal thinking process with efficient reasoning and reflections. You don't have a strict token budget but be less verbose and more direct in your thinking. \nNo think mode: Respond directly to the question without any internal reasoning process or extra thinking tokens. Still follow the template with the minimum required thinking tokens to justify the answer. \nBudgeted think mode: Limit your internal reasoning and reflections to stay within the specified token budget\n\nBased on the complexity of the problem, select the appropriate mode for reasoning among the provided options listed below.\n \nProvided Mode(s):\nEfficient think."
    },
    {
        "role": "system",
        "content": "You are provided with a task description, a history of previous actions, and corresponding screenshots. Your goal is to perform the next action to complete the task. Please note that if performing the same action multiple times results in a static screen with no changes, you should attempt a modified or alternative action."
    },
    {
        "role": "system",
        "content": "## Function Definition\n\n- You have access to the following functions:\n{\"type\": \"function\", \"name\": \"call_user\", \"parameters\": {\"type\": \"object\", \"properties\": {\"content\": {\"type\": \"string\", \"description\": \"Message or information displayed to the user to request their input, feedback, or guidance.\"}}, \"required\": []}, \"description\": \"This function is used to interact with the user by displaying a message and requesting their input, feedback, or guidance.\"}\n{\"type\": \"function\", \"name\": \"click\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Click coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse left single click action.\"}\n{\"type\": \"function\", \"name\": \"drag\", \"parameters\": {\"type\": \"object\", \"properties\": {\"start_point\": {\"type\": \"string\", \"description\": \"Drag start point. The format is: <point>x y</point>\"}, \"end_point\": {\"type\": \"string\", \"description\": \"Drag end point. The format is: <point>x y</point>\"}}, \"required\": [\"start_point\", \"end_point\"]}, \"description\": \"Mouse left button drag action.\"}\n{\"type\": \"function\", \"name\": \"finished\", \"parameters\": {\"type\": \"object\", \"properties\": {\"content\": {\"type\": \"string\", \"description\": \"Provide the final answer or response to complete the task.\"}}, \"required\": []}, \"description\": \"This function is used to indicate the completion of a task by providing the final answer or response.\"}\n{\"type\": \"function\", \"name\": \"hotkey\", \"parameters\": {\"type\": \"object\", \"properties\": {\"key\": {\"type\": \"string\", \"description\": \"Hotkeys you want to press. Split keys with a space and use lowercase.\"}}, \"required\": [\"key\"]}, \"description\": \"Press hotkey.\"}\n{\"type\": \"function\", \"name\": \"left_double\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Click coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse left double click action.\"}\n{\"type\": \"function\", \"name\": \"mouse_down\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Mouse down position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>\"}, \"button\": {\"type\": \"string\", \"description\": \"Down button. Default to left.\", \"enum\": [\"left\", \"right\"]}}, \"required\": []}, \"description\": \"Mouse down action.\"}\n{\"type\": \"function\", \"name\": \"mouse_up\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Mouse up position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>\"}, \"button\": {\"type\": \"string\", \"description\": \"Up button. Default to left.\", \"enum\": [\"left\", \"right\"]}}, \"required\": []}, \"description\": \"Mouse up action.\"}\n{\"type\": \"function\", \"name\": \"move_to\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Target coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse move action.\"}\n{\"type\": \"function\", \"name\": \"open_computer\", \"parameters\": {}, \"description\": \"Open computer.\"}\n{\"type\": \"function\", \"name\": \"open_computer\", \"parameters\": {}, \"description\": \"Open computer.\"}\n{\"type\": \"function\", \"name\": \"press\", \"parameters\": {\"type\": \"object\", \"properties\": {\"key\": {\"type\": \"string\", \"description\": \"Key you want to press. Only one key can be pressed at one time.\"}}, \"required\": [\"key\"]}, \"description\": \"Press key.\"}\n{\"type\": \"function\", \"name\": \"release\", \"parameters\": {\"type\": \"object\", \"properties\": {\"key\": {\"type\": \"string\", \"description\": \"Key you want to release. Only one key can be released at one time.\"}}, \"required\": [\"key\"]}, \"description\": \"Release key.\"}\n{\"type\": \"function\", \"name\": \"right_single\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Click coordinates. The format is: <point>x y</point>\"}}, \"required\": [\"point\"]}, \"description\": \"Mouse right single click action.\"}\n{\"type\": \"function\", \"name\": \"scroll\", \"parameters\": {\"type\": \"object\", \"properties\": {\"point\": {\"type\": \"string\", \"description\": \"Scroll start position. If not specified, default to execute on the current mouse position. The format is: <point>x y</point>\"}, \"direction\": {\"type\": \"string\", \"description\": \"Scroll direction.\", \"enum\": [\"up\", \"down\", \"left\", \"right\"]}}, \"required\": [\"direction\"]}, \"description\": \"Scroll action.\"}\n{\"type\": \"function\", \"name\": \"take_screenshot\", \"parameters\": {}, \"description\": \"Take screenshot.\"}\n{\"type\": \"function\", \"name\": \"type\", \"parameters\": {\"type\": \"object\", \"properties\": {\"content\": {\"type\": \"string\", \"description\": \"Type content. If you want to submit your input, use \\n at the end of content.\"}}, \"required\": [\"content\"]}, \"description\": \"Type content.\"}\n{\"type\": \"function\", \"name\": \"wait\", \"parameters\": {\"type\": \"object\", \"properties\": {\"time\": {\"type\": \"integer\", \"description\": \"Wait time in seconds.\"}}, \"required\": []}, \"description\": \"Wait for a while.\"}\n\n- To call a function, use the following structure without any suffix:\n\n<gui_think> reasoning process </gui_think>\n<seed:tool_call><function=example_function_name><parameter=example_parameter_1>value_1</parameter><parameter=example_parameter_2>\nThis is the value for the second parameter\nthat can span\nmultiple lines\n</parameter></function></seed:tool_call>\n\n## Important Notes\n- Function calls must begin with <function= and end with </function>.\n- All required parameters must be explicitly provided.\n\n## Additional Notes\n- You can execute multiple actions within a single tool call. For example:\n<seed:tool_call><function=example_function_1><parameter=example_parameter_1>value_1</parameter><parameter=example_parameter_2>\nThis is the value for the second parameter\nthat can span\nmultiple lines\n</parameter></function><function=example_function_2><parameter=example_parameter_3>value_4</parameter></function></seed:tool_call>"
    },
    {
        "role": "user",
        "content": "Click the chrome icon."
    },
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            }
        ]
    }
]

# infer and post process

content = inference(messages)
print("==========Model Prediction==========")
print(content)
tool_calls = parse_xml_action_v2(content, tool_schemas)
actions = []
for tool_call in tool_calls:
    actions.append(
        {
            "action_type": tool_call["function"],
            "action_inputs": tool_call["parameters"]
        }
    )
image_height = image.height
image_width = image.width
pyautogui_code = parsing_response_to_pyautogui_code(actions, image_height, image_width)

print("==============Pyautogui Code============")
print(pyautogui_code)