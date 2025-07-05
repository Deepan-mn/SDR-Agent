"""
 @Author  Deeps (11678)
 @email   deepan.mn@zohocorp.com
 @Date   18/11/24

"""
import traceback
import uuid
import streamlit as st
from colorama import Fore, Style

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from src.workflow.graph import Workflow

# Load all env variables
load_dotenv()

llm = ChatGroq(model_name="llama-3.1-70b-versatile", temperature=0.1)
# llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)

# config
# config = {}
# thread_id = str(uuid.uuid4())
thread_id = "1"
config = {
    "configurable": {
        "thread_id": thread_id,
    },
    'recursion_limit': 100
}

workflow = Workflow(llm)
app = workflow.app

initial_state = {
    "emails": [],
    "current_email": {
        "id": "",
        "sender": "",
        "name":"",
        "subject": "",
        "body": ""
    },
    "email_category": "",
    "generated_email": "",
    "rag_questions": [],
    "retrieved_infos": "",
    "lead_info":"",
    "lead_name":"",
    "company_name":"zoho",
    "lead_mail":"customer.johnnydepp@gmail.com",
    "lead_info_summary": "",
    "welcome_email":"",
    "welcome_trails":0,
    "review": "",
    "call_scheduled":"",
    "welcome_email_review":"",
    "owner_id": "",
    "record_id": "",
    "call_subject":"",
    "call_purpose":"",
    "call_date_time":"",
    "call_description":"",
    "lead_qualified":"False",
    "lead_status":"Not Qualified",
    "lead_type":"new",
    "trials": 0,
    "contact_created":""
}



# ## plot
# from IPython.display import Image, display
#
# try:
#     graph_png = app.get_graph().draw_png()
#     with open("output_graph.png", "wb") as f:
#         f.write(graph_png)
#     display(Image(graph_png))
#     print("Graph saved as 'output_graph.png'")
# except ImportError:
#     print(
#         "You likely need to install dependencies for pygraphviz, see more here https://github.com/pygraphviz/pygraphviz/blob/main/INSTALL.txt"
#     )

# try:
#     # Run the automation
#     print(Fore.GREEN + "Starting workflow..." + Style.RESET_ALL)
#     for output in app.stream(initial_state, config):
#         for key, value in output.items():
#             print(Fore.CYAN + f"Finished running: {key}:" + Style.RESET_ALL)
# except Exception as e:
#     print(e)
#     print(traceback.format_exc())


# Streamlit App
st.title("Lead Nurturing Autonomous Agent")

# Form to collect input data
with st.form("lead_form"):
    lead_mail = st.text_input("Lead Email", value="customer.johnnydepp@gmail.com")
    lead_company_name = st.text_input("Company Name", value="zoho")
    record_id = st.text_input("Record ID", value="")
    upload_data = st.multiselect("Organization Informations",options=["About Company","Product Knowledge","FAQs",])
    # Submit button
    submitted = st.form_submit_button("Run Workflow")

if submitted:
    try:
        # Populate initial state with form data
        initial_state = initial_state.copy()
        initial_state.update({

            "lead_mail": lead_mail,
            "company_name": lead_company_name,
            "record_id":record_id
        })
        print(initial_state)

        # Config
        thread_id = str(uuid.uuid4())
        config = {
            "configurable": {
                "thread_id": thread_id,
            },
            'recursion_limit': 100
        }
        # Render graph
        graph_png = app.get_graph().draw_png()
        with open("output_graph.png", "wb") as f:
            f.write(graph_png)
        st.image("output_graph.png", caption="Workflow Graph")

        # Run the workflow
        st.success("Running workflow...")
        results = []
        for output in app.stream(initial_state, config):
            for key, value in output.items():
                results.append((key, value))

        st.write("Workflow Results:")
        for key, value in results:
            st.write(f"**{key}**: {value}")



    except Exception as e:
        st.error("An error occurred during workflow execution.")
        st.text(traceback.format_exc())


