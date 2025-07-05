import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.workflow.node import Nodes
from src.workflow.state import GraphState


class Workflow():
    def __init__(self, llm):
        # initiate graph state & nodes
        workflow = StateGraph(GraphState)
        nodes = Nodes(llm)

        # define all graph nodes
        workflow.add_node("analyze_lead_info", nodes.analyze_lead_info)
        workflow.add_node("scrape_company_info", nodes.scrape_company_profile)

        # Outreach email nodes
        workflow.add_node("write_outreach_mail", nodes.write_welcome_email)
        workflow.add_node("verify_welcome_email", nodes.verify_welcome_email)
        workflow.add_node("send_welcome_email", nodes.send_welcome_email)

        # email extraction nodes
        workflow.add_node("load_new_emails", nodes.load_new_emails)
        workflow.add_node("extract_email_sentiment", nodes.extract_sentiment)
        workflow.add_node("extract_email_intent", nodes.extract_intent)
        workflow.add_node("extract_email_interest", nodes.extract_interest)
        workflow.add_node("extract_email_emotion", nodes.extract_emotion)

        workflow.add_node("categorize_email", nodes.categorize_email)

        # call related nodes
        workflow.add_node("generate_call_subject", nodes.generate_call_subject)
        workflow.add_node("generate_call_description", nodes.generate_call_description)
        workflow.add_node("extract_call_purpose", nodes.extract_call_purpose)
        workflow.add_node("extract_call_date_time", nodes.extract_call_date_time)
        workflow.add_node("schedule_call", nodes.schedule_call)

        # Information construction nodes
        workflow.add_node("construct_rag_questions", nodes.construct_rag_questions)
        workflow.add_node("retrieve_from_rag", nodes.retrieve_from_rag)
        workflow.add_node("write_draft_email", nodes.write_draft_email)
        workflow.add_node("verify_generated_email", nodes.verify_generated_email)
        workflow.add_node("create_draft_response_and_send", nodes.send_email_response)


        # Qualify tools
        workflow.add_node("lead_qualifier", nodes.lead_qualifier)
        workflow.add_node("listener", nodes.status_listener)
        workflow.add_node("convert_to_contact", nodes.convert_to_contact)
        # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

        workflow.set_entry_point("analyze_lead_info")
        # workflow.add_edge("scrape_company_info", "write_outreach_mail")

        workflow.add_conditional_edges(
            "analyze_lead_info",
            nodes.route_to_scarpe_based_on_input,
            {
                "process": "scrape_company_info",
                "skip": "listener"}

        )

        workflow.add_edge("scrape_company_info", "write_outreach_mail")
        workflow.add_edge("write_outreach_mail", "verify_welcome_email")
        workflow.add_conditional_edges(
            "verify_welcome_email",
            nodes.must_rewrite_welcome_mail,
            {
                "send": "send_welcome_email",
                "rewrite": "write_outreach_mail",
                "stop": "write_outreach_mail"
            }
        )

        workflow.add_edge("send_welcome_email", "listener")
        workflow.add_conditional_edges(
            "load_new_emails",
            nodes.check_new_emails,
            {
                "process": "extract_email_sentiment",
                "stop": "lead_qualifier"
            }
        )

        # workflow.add_edge("load_new_emails", "lead_qualifier")
        workflow.add_edge("lead_qualifier", "listener")

        # check if there are email to process
        workflow.add_conditional_edges(
            "listener",
            nodes.route_based_on_listener,
            {
                "process": "load_new_emails",
                "stop": "convert_to_contact"
            }
        )
        workflow.add_edge("convert_to_contact", END)
        # # check if there are email to process
        # workflow.add_conditional_edges(
        #     "load_new_emails",
        #     nodes.check_new_emails,
        #     {
        #         "process": "extract_email_sentiment",
        #         "empty": "listener"
        #     }
        # )


        workflow.add_edge("load_new_emails", "extract_email_sentiment")
        workflow.add_edge("extract_email_sentiment", "extract_email_intent")
        workflow.add_edge("extract_email_intent", "extract_email_interest")
        workflow.add_edge("extract_email_interest", "extract_email_emotion")
        workflow.add_edge("extract_email_emotion", "categorize_email")

        # route email based on category
        workflow.add_conditional_edges(
            "categorize_email",
            nodes.route_email_based_on_category,
            {
                "product related": "construct_rag_questions",
                "not product related": "write_draft_email",
                "call_request": "generate_call_subject"
            }
        )
        workflow.add_edge("generate_call_subject", "generate_call_description")
        workflow.add_edge("generate_call_description", "extract_call_purpose")
        workflow.add_edge("extract_call_purpose", "extract_call_date_time")
        workflow.add_edge("extract_call_date_time", "schedule_call")
        workflow.add_edge("schedule_call", "lead_qualifier")

        # pass constructed query to RAG chain to get informations
        workflow.add_edge("construct_rag_questions", "retrieve_from_rag")
        # give information to writer agent to create draft email
        workflow.add_edge("retrieve_from_rag", "write_draft_email")
        # verify the create draft email
        workflow.add_edge("write_draft_email", "verify_generated_email")
        # check if email is send-able or not, if not rewrite the email
        workflow.add_conditional_edges(
            "verify_generated_email",
            nodes.must_rewrite,
            {
                "send": "create_draft_response_and_send",
                "rewrite": "write_draft_email",
                "stop": "categorize_email"
            }
        )

        workflow.add_edge("create_draft_response_and_send", "lead_qualifier")

        # check if there are still emails to be processed
        # workflow.add_edge("create_draft_response_and_send", END)

        memory = MemorySaver()

        # Compile
        self.app = workflow.compile(checkpointer=memory)

