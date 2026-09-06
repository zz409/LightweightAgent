import dotenv
import openai
import os
import json
import pathlib

dotenv.load_dotenv()

if __name__=="__main__":
    api_key=os.getenv("API_KEY")
    base_url=os.getenv("BASE_URL")

    client=openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    WORKSPACE=pathlib.Path("generated_site")
    WORKSPACE.mkdir(exist_ok=True)

    def write_file(path,content):
        file_path=WORKSPACE/path

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path.write_text(
            content,
            encoding="utf-8"
        )

        return f"write success: {path}"

    def read_file(path):
        file_path=WORKSPACE/path
        return file_path.read_text(encoding="utf8")

    def list_files():
        file=[]

        for path in WORKSPACE.rglob("*"):
            if path.is_file():
                file.append(str(path.relative_to(WORKSPACE)))
        return "\n".join(file)

    tools=[
        {
            "type":"function",
            "function":{
                "name":"write_file",
                "description":"create or modify a file",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "path":{
                            "type":"string"
                        },
                        "content":{
                            "type":"string"
                        }
                    },

                    "required":[
                        "path",
                        "content"
                    ]
                }
            }
        },

        {
            "type":"function",
            "function":{
                "name":"read_file",
                "description":"read a file",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "path":{
                            "type":"string"
                        }
                    },

                    "required":[
                        "path"
                    ]
                }
            }
        },

        {
            "type":"function",
            "function":{
                "name":"list_files",
                "description":"list all files",
                "parameters":{
                    "type":"object",
                    "properties":{}
                }
            }
        }
    ]

    def execute_tool(name,arguments):
        if name=="write_file":
            return write_file(
                path=arguments["path"],
                content=arguments["content"]
            )

        if name=="read_file":
            return read_file(
                arguments["path"]
            )

        if name=="list_files":
            return list_files()

    messages=[
        {
            "role":"system",
            "content":"""
            You are a Code Agent.
            Generate the corresponding code based on the user's request.
            You can use the tools to read and write files.
            Don't simply tell the user the code,you must use 'write_file' to actually create the files.
            You may decide for yourself which HTML,CSS,and JavaScript files to create.
            Inform the user once the code generation is complete.
            """
        }
    ]

    def run_agent(user_request):
        messages.append(
            {
                "role":"user",
                "content":user_request
            }
        )

        while True:
            response=client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=messages,
                tools=tools
            )

            message=response.choices[0].message

            messages.append(message)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                name=tool_call.function.name
                arguments=json.loads(
                    tool_call.function.arguments
                )

                result=execute_tool(
                    name,
                    arguments
                )

                print(result)

                messages.append(
                    {
                        "role":"tool",
                        "tool_call_id":tool_call.id,
                        "content":result
                    }
                )

    while True:
        user_request=input("\nYou:")
        if user_request=="exit":
            break
        run_agent(user_request)
