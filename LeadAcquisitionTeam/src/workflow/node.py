import os
import time

from colorama import Fore, Style

from src.agents.agents import Agents
from src.tools.CallScheduleTools import CallScheduleTools
from src.tools.CompanyProfileSourcingTools import CompanyProfileTool
from src.tools.GmailTools import GmailToolsClass
from src.tools.OutReachTools import OutReachTool
from src.tools.UserProfileSourcingTools import UserProfileTools
from src.workflow.state import GraphState, Email
from src.tools.ContactCreateTools import CreateContactTools


class Nodes:
    def __init__(self, llm):
        self.agents = Agents(llm)
        self.gmail_tools = GmailToolsClass()
        # self.user_source_tools = UserProfileTools()
        self.company_source_tools = CompanyProfileTool()
        self.outreach_tools = OutReachTool()
        self.callTools = CallScheduleTools()
        self.contactTools = CreateContactTools()

    def analyze_lead_info(self, state: GraphState) -> GraphState:
        """
        Scrape the user information from the linkedin
        @param state: The current state of the graph.
        @return: Updated state with new emails.
        """
        print(Fore.YELLOW + "Analyzing the Led type...\n" + Style.RESET_ALL)
        return {**state,"lead_type":"new"}

    def route_to_scarpe_based_on_input(self, state: GraphState) -> str:
        print(Fore.YELLOW + "Routing scraping based on lead type...\n" + Style.RESET_ALL)
        if state["lead_type"] == "new":
            return "process"
        else:
            return "skip"

    # def scrape_user_profile(self,state: GraphState) -> GraphState:
    #     """
    #     Scrape the user information from the linkedin
    #     @param state: The current state of the graph.
    #     @return: Updated state with new emails.
    #     """
    #     print(Fore.YELLOW + "Scrapping user information...\n" + Style.RESET_ALL)
    #     lead_info = self.user_source_tools.fetch_user_profile(state["lead_name"])
    #     user_scrapped_result = self.agents.lead_user_profile_summary.invoke({'lead_info':state["lead_info"]})
    #     print(Fore.MAGENTA + "User Info scrapped:" + Style.RESET_ALL, user_scrapped_result)
    #     return {**state,"lead_info_summary": user_scrapped_result, "lead_info":lead_info}

    def scrape_company_profile(self, state: GraphState) -> GraphState:
        """
        Scrape the user information from the linkedin
        @param state: The current state of the graph.
        @return: Updated state with new emails.
        """
        print(Fore.YELLOW + "Scrapping Company information...\n" + Style.RESET_ALL)
        lead_info_dict = self.company_source_tools.fetch_company_profile(state["company_name"])
        print(state["company_name"])
        print(lead_info_dict['overview_text'])
        company_scrapped_result = self.agents.company_profile_summary.invoke(
            {'lead_info': lead_info_dict["overview_text"]})
        print(Fore.MAGENTA + "Company Info scrapped:" + Style.RESET_ALL, company_scrapped_result)
        return {**state, "lead_info_summary": company_scrapped_result, "lead_info": lead_info_dict}

    def write_welcome_email(self, state: GraphState) -> GraphState:
        """
        Writes a draft welcome email based on the lead informations

        @param state: The current state of the graph.
        @return: Updated state with generated email and trial count.
        """
        print(Fore.YELLOW + "Writing welcome email...\n" + Style.RESET_ALL)
        welcome_email_result = self.agents.welcome_email.invoke({
            "name": state["company_name"],
            "lead_info": state["lead_info_summary"]
        })
        welcome_email = welcome_email_result["email"]
        trials = state.get('welcome_trails', 0) + 1
        return {
            **state,
            "welcome_email": welcome_email,
            "welcome_trails": trials
        }

    def verify_welcome_email(self, state: GraphState) -> GraphState:
        """
        Verifies the welcome email using the verify_email agent.

        @param state: The current state of the graph.
        @return: Updated state with email review.
        """
        print(Fore.YELLOW + "Verifying generated email...\n" + Style.RESET_ALL)
        verify_welcome_result = self.agents.verify_welcome_email.invoke(
            {
                "lead_info": state["lead_info_summary"],
                "welcome_email": state["welcome_email"]
            }
        )
        review = verify_welcome_result["welcome_email_review"]
        return {**state, "welcome_email_review": review}

    def must_rewrite_welcome_mail(self, state: GraphState) -> str:
        """
        Determines if the email needs to be rewritten based on the review and trial count.

        @param state: The current state of the graph.
        @return: 'send' if email is good, 'stop' if max trials reached, 'rewrite' otherwise.
        """
        review = state["welcome_email_review"]
        if review == "send":
            print(Fore.GREEN + "Welcome Email is good, ready to be sent!!!" + Style.RESET_ALL)
            # state["welcome_email"].pop()
            return "send"
        elif state["trials"] >= 10:
            print(Fore.RED + "Welcome Email is not good, we reached max trials must stop!!!" + Style.RESET_ALL)
            state["emails"].pop()
            return "stop"
        else:
            print(Fore.RED + "Welcome Email is not good, must rewrite it..." + Style.RESET_ALL)
            return "rewrite"

    def draft_welcome_email(self, state: GraphState) -> GraphState:
        """
        Creates a draft welcome email in Gmail.

        @param state: The current state of the graph.
        @return: Updated state with reset trial count.
        """
        print(Fore.YELLOW + "Creating draft welcome email...\n" + Style.RESET_ALL)
        self.outreach_tools.draft_welcome_mail(
            state["lead_info_summary"],
            state["lead_mail"],
            state["welcome_email"]
        )
        return {"trials": 0,"lead_type":"old"}

    def send_welcome_email(self, state: GraphState) -> GraphState:
        """
        Creates a draft welcome email in Gmail.

        @param state: The current state of the graph.
        @return: Updated state with reset trial count.
        """
        print(Fore.YELLOW + "Sending Welcome email...\n" + Style.RESET_ALL)
        self.outreach_tools.send_welcome_mail(
            state["lead_info_summary"],
            state["lead_mail"],
            state["welcome_email"]
        )
        return {"trials": 0,"lead_type":"old"}

    def load_new_emails(self, state: GraphState) -> GraphState:
        """
        Loads new emails from Gmail and updates the state.

        @param state: The current state of the graph.
        @return: Updated state with new emails.
        """
        emails = []
        print(Fore.YELLOW + "Loading new emails...\n" + Style.RESET_ALL)
        recent_emails = self.gmail_tools.fetch_recent_emails()
        # Only keep received emails
        try:
            emails = [Email(**email) for email in recent_emails if (os.environ['MY_EMAIL'] not in email['sender'])]
            print("The cls", emails)
            # emails = [emails[0]]  # first - Recent mail is taken
            print("The after ", emails)
        except Exception as e:
            print(e)
        current_email =emails[0]
        return {**state, "emails": emails ,"current_email": current_email}



    def extract_sentiment(self, state: GraphState) -> GraphState:
        """
        Extracts sentiment from email.
        @param state: The current state of the graph.
        @return: Updated state with email sentiment.
        """
        print(Fore.YELLOW + "Extracting Sentiments from email...\n" + Style.RESET_ALL)
        print("The done  email is: ", state["current_email"])
        current_email = state["current_email"]
        print("The email is: ", current_email)
        sentiment_result = self.agents.extract_email_sentiment.invoke({"email": current_email.body})
        print(sentiment_result)
        print(Fore.MAGENTA + "Email Sentiments:" + Style.RESET_ALL, sentiment_result["sentiment"])

        return {**state, "email_sentiment": sentiment_result["sentiment"]}

    def extract_intent(self, state: GraphState) -> GraphState:
        """
        Extracts intent from email.
        @param state: The current state of the graph.
        @return: Updated state with email intent.
        """
        print(Fore.YELLOW + "Extracting Intent from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        print("The email is: ", current_email)
        intent_result = self.agents.extract_email_intent.invoke({"email": current_email.body})
        print(intent_result)
        print(Fore.MAGENTA + "Email Intent:" + Style.RESET_ALL, intent_result["intent"])
        return {**state, "email_intent": intent_result["intent"]}

    def extract_interest(self, state: GraphState) -> GraphState:
        """
        Extracts interest from email.
        @param state: The current state of the graph.
        @return: Updated state with email interest.
        """
        print(Fore.YELLOW + "Extracting Interest level from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        interest_result = self.agents.extract_email_interest.invoke({"email": current_email.body})
        print(interest_result)
        print(Fore.MAGENTA + "Email Interest level:" + Style.RESET_ALL, interest_result["interest"])
        return {**state, "email_interest": interest_result["interest"]}

    def extract_emotion(self, state: GraphState) -> GraphState:
        """
        Extracts emotion from email.
        @param state: The current state of the graph.
        @return: Updated state with email emotions.
        """
        print(Fore.YELLOW + "Extracting Emotion  from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        emotion_result = self.agents.extract_email_emotion.invoke({"email": current_email.body})
        print(emotion_result)
        print(Fore.MAGENTA + "Email Emotion :" + Style.RESET_ALL, emotion_result["emotion"])
        return {**state, "email_emotion": emotion_result["emotion"]}

    def generate_call_subject(self, state: GraphState) -> GraphState:
        """
        generate call subject from email.

        @param state: The current state of the graph.
        @return: Updated state with call_subject.
        """
        print(Fore.YELLOW + "Generating Subjects from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        print("Current_email: ", current_email)
        print("Current_email body: ", current_email.body)
        call_subject_result = self.agents.generate_call_subject.invoke({"email": current_email.body})
        print(call_subject_result)
        print(Fore.MAGENTA + "Call subject:" + Style.RESET_ALL, call_subject_result["call_subject"])
        return {**state, "call_subject": call_subject_result["call_subject"]}

    def generate_call_description(self, state: GraphState) -> GraphState:
        """
        generate call subject from email.

        @param state: The current state of the graph.
        @return: Updated state with call_description.
        """
        print(Fore.YELLOW + "Generating description from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        call_description_result = self.agents.generate_call_description.invoke({"email": current_email.body})
        print(call_description_result)
        print(Fore.MAGENTA + "Call Description:" + Style.RESET_ALL, call_description_result["call_description"])
        return {**state, "call_description": call_description_result["call_description"]}

    def extract_call_purpose(self, state: GraphState) -> GraphState:
        """
        extract the call purpose from email.

        @param state: The current state of the graph.
        @return: Updated state with call_purpose .
        """
        print(Fore.YELLOW + "Extracting call purpose from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        call_description_result = self.agents.extract_call_purpose.invoke({"email": current_email.body})
        print(call_description_result)
        print(Fore.MAGENTA + "Call Purpose:" + Style.RESET_ALL, call_description_result["call_category"])
        return {**state, "call_purpose": call_description_result["call_category"]}

    def extract_call_date_time(self, state: GraphState) -> GraphState:
        """
        extract the call purpose from email.

        @param state: The current state of the graph.
        @return: Updated state with call date_time.
        """
        print(Fore.YELLOW + "Extracting call date_time from email...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        call_date_time_result = self.agents.extract_call_date_time.invoke({"email": current_email.body})
        print(call_date_time_result)
        print(Fore.MAGENTA + "Call Date/Time:" + Style.RESET_ALL, call_date_time_result["call_date_time"])
        return {**state, "call_date_time": call_date_time_result["call_date_time"]}

    def schedule_call(self, state: GraphState) -> GraphState:
        """
        Schedule a call based on the available information in zoho crm
        @param state: The current state of the graph.
        @return: scheduled or not scheduled.
        """
        print(Fore.YELLOW + "Scheduling call...\n" + Style.RESET_ALL)
        if self.callTools.schedule_call(
                record_id=state['record_id'],
                description=state['call_description'],
                start_time=state['call_date_time'],
                subject=state['call_subject'],
                purpose=state['call_purpose']):
            return {**state, "call_scheduled": "True"}
        else:
            return {**state, "call_scheduled": "False"}

    def check_new_emails(self, state: GraphState) -> str:
        """
        Checks if there are new emails to process.

        @param state: The current state of the graph.
        @return: 'process' if there are new emails, 'empty' otherwise.
        """
        # self._update_current_email(state)
        if len(state['emails']) == 0:
            print(Fore.RED + "No new emails" + Style.RESET_ALL)
            return "empty"
        else:
            print(Fore.GREEN + "New emails to process" + Style.RESET_ALL)
            return "process"

    # def _update_current_email(self, state: GraphState) -> GraphState:


    def categorize_email(self, state: GraphState) -> GraphState:
        """
        Categorizes the current email using the categorize_email agent.

        @param state: The current state of the graph.
        @return: Updated state with email category.
        """
        print(Fore.YELLOW + "Checking email category...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        category_result = self.agents.categorize_email.invoke({"email": current_email.body})
        print("\n\n\n")
        print(category_result)
        print(current_email)
        print(current_email.body)
        print("\n\n\n\n")

        print(Fore.MAGENTA + "Email category:" + Style.RESET_ALL, category_result["category"])
        return {
            **state,
            "email_category": category_result["category"],
            "current_email": current_email
        }

    def route_email_based_on_category(self, state: GraphState) -> str:
        """
        Routes the email based on its category.

        @param state: The current state of the graph.
        @return: 'product related' or 'not product related' based on the email category.
        """
        print(Fore.YELLOW + "Routing email based on category...\n" + Style.RESET_ALL)
        category = state["email_category"]
        if category == "product_enquiry":
            return "product related"
        elif category == "call_request":
            return "call_request"
        else:
            return "not product related"

    def construct_rag_questions(self, state: GraphState) -> GraphState:
        """
        Constructs RAG questions based on the email content.

        @param state: The current state of the graph.
        @return: Updated state with RAG questions.
        """
        print(Fore.YELLOW + "Designing RAG query...\n" + Style.RESET_ALL)
        email_content = state["current_email"].body
        query_result = self.agents.design_rag_query.invoke({"email": email_content})
        return {**state, "rag_questions": query_result["query"]}

    def retrieve_from_rag(self, state: GraphState) -> GraphState:
        """
        Retrieves information from internal knowledge based on RAG questions.

        @param state: The current state of the graph.
        @return: Updated state with retrieved information.
        """
        print(Fore.YELLOW + "Retrieving information from internal knowledge...\n" + Style.RESET_ALL)
        queries = state["rag_questions"]
        final_answer = ""
        for query in queries:
            rag_result = self.agents.retrieve_docs.invoke(query)
            final_answer += query + "\n" + rag_result + "\n\n"
        return {**state, "retrieved_documents": final_answer}

    def write_draft_email(self, state: GraphState) -> GraphState:
        """
        Writes a draft email based on the current email and retrieved information.

        @param state: The current state of the graph.
        @return: Updated state with generated email and trial count.
        """
        if state["email_category"] == "unrelated":
            information = {**state, "retrieved_documents": ""}
        else:
            information = state["retrieved_documents"]
        print(Fore.YELLOW + "Writing draft email...\n" + Style.RESET_ALL)
        draft_result = self.agents.write_draft_email.invoke({
            "email": state["current_email"].body,
            "subject": state["current_email"].subject,
            "name": state["current_email"].name,
            "category": state["email_category"],
            "informations": information
        })
        email = draft_result["email"]
        trials = state.get('trials', 0) + 1
        return {
            **state,
            "generated_email": email,
            "trials": trials
        }

    def verify_generated_email(self, state: GraphState) -> GraphState:
        """
        Verifies the generated email using the verify_email agent.

        @param state: The current state of the graph.
        @return: Updated state with email review.
        """
        if state["email_category"] == "unrelated":
            information = {**state, "retrieved_documents": ""}
        else:
            information = state["retrieved_documents"]
        print(Fore.YELLOW + "Verifying generated email...\n" + Style.RESET_ALL)
        verify_result = self.agents.verify_email.invoke({
            "initial_email": state["current_email"].body,
            "category": state["email_category"],
            "generated_email": state["generated_email"],
            "informations": information
        })
        review = verify_result["review"]
        return {**state, "review": review}

    def must_rewrite(self, state: GraphState) -> str:
        """
        Determines if the email needs to be rewritten based on the review and trial count.

        @param state: The current state of the graph.
        @return: 'send' if email is good, 'stop' if max trials reached, 'rewrite' otherwise.
        """
        review = state["review"]
        if review == "send":
            print(Fore.GREEN + "Email is good, ready to be sent!!!" + Style.RESET_ALL)
            state["emails"].pop()
            return "send"
        elif state["trials"] >= 10:
            print(Fore.RED + "Email is not good, we reached max trials must stop!!!" + Style.RESET_ALL)
            state["emails"].pop()
            return "stop"
        else:
            print(Fore.RED + "Email is not good, must rewrite it..." + Style.RESET_ALL)
            return "rewrite"

    def create_draft_response(self, state: GraphState) -> GraphState:
        """
        Creates a draft response in Gmail.

        @param state: The current state of the graph.
        @return: Updated state with reset trial count.
        """
        print(Fore.YELLOW + "Creating draft email...\n" + Style.RESET_ALL)
        self.gmail_tools.create_draft_reply(
            state["current_email"].id,
            state["current_email"].sender,
            f"Re: {state['current_email'].subject}",
            state["generated_email"]
        )
        return {"trials": 0}

    def send_email_response(self, state: GraphState) -> GraphState:
        """
        Sends the email response directly using Gmail.

        @param state: The current state of the graph.
        @return: Updated state with reset trial count.
        """
        print(Fore.YELLOW + "Sending email...\n" + Style.RESET_ALL)
        self.gmail_tools.send_reply(
            state["current_email"].id,
            state["current_email"].sender,
            f"Re: {state['current_email'].subject}",
            state["generated_email"]
        )
        return {"trials": 0}

    def lead_qualifier(self, state: GraphState) -> GraphState:
        """
        Sends the email response directly using Gmail.

        @param state: The current state of the graph.
        @return: Updated state with lead_qualification.
        """
        print(Fore.YELLOW + "Lead qualifier is Analyzing ...\n" + Style.RESET_ALL)
        current_email = state["current_email"]
        lead_qualifier_result = self.agents.lead_qualify_status.invoke({"email": current_email.body})
        print(Fore.MAGENTA + "Lead Qualification Status:" + Style.RESET_ALL, lead_qualifier_result["lead_status"])
        return {**state, "lead_status": lead_qualifier_result["lead_status"]}

    def status_listener(self, state: GraphState):
        """
        Analyze the status of the lead
        @param state: The current state of the graph.
        @return: Updated state with reset trial count.
        """
        print(Fore.YELLOW + "Listener is waiting for Reply ...\n" + Style.RESET_ALL)
        if state["lead_status"] =="Qualified":
            return {**state,"lead_qualified":"True"}
        else:
            return  {**state,"lead_qualified":"False"}
        print(Fore.MAGENTA + "Listener Status:" + Style.RESET_ALL, state["lead_qualified"])

    def route_based_on_listener(self, state: GraphState) -> str:
        """
        Analyze the status of the lead
        @param state: The current state of the graph.
        @return: Updated state with reset trial count.
        """
        if state['lead_status'] == "Not Qualified":
            time.sleep(100)
            return "process"
        else:
            return "stop"

    def convert_to_contact(self,state:GraphState)->GraphState:
        print(Fore.YELLOW + "Scheduling call...\n" + Style.RESET_ALL)
        if self.contactTools.convert_to_contact(
               contact_name=state["current_email"].name):
            return {**state, "contact_created": "True"}
        else:
            return {**state, "contact_created": "False"}

