
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from src.prompts.prompts import *


class Agents():
    def __init__(self, llm):
        # QA assistant chat
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vectorstore = Chroma(persist_directory="db", embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        qa_prompt = ChatPromptTemplate.from_template(qa_prompt_template)
        self.retrieve_docs = (
                {"context": retriever, "question": RunnablePassthrough()}
                | qa_prompt
                | llm
                | StrOutputParser()
        )
        # lead user profile sourcing chain
        # user_profile_prompt = PromptTemplate(
        #     template=lead_info_prompt_template,
        #     input_variables=["lead_info"]
        # )
        # self.lead_user_profile_summary = user_profile_prompt | llm | JsonOutputParser()

        # lead company profile sourcing chain
        company_profile_prompt = PromptTemplate(
            template=lead_info_prompt_template,
            input_variables=["lead_info"]
        )
        self.company_profile_summary = company_profile_prompt | llm | JsonOutputParser()

        # Used to write a draft welcome email based on lead_information
        welcome_email_prompt = PromptTemplate(
            template=draft_welcome_email_prompt_template,
            input_variables=["name","lead_info"]
        )
        self.welcome_email = welcome_email_prompt | llm | JsonOutputParser()

        # Verify the generated welcome email
        verify_welcome_email_prompt = PromptTemplate(
            template=verify_welcome_prompt_template,
            input_variables=[ "lead_info","welcome_email"]
        )
        self.verify_welcome_email = verify_welcome_email_prompt | llm | JsonOutputParser()

        # extract sentiment from the email
        email_sentiment_analyzer_prompt = PromptTemplate(
            template=email_sentiment_analyzer_prompt_template,
            input_variables=["email"]
        )
        self.extract_email_sentiment = email_sentiment_analyzer_prompt | llm | JsonOutputParser()

        # extract intent from the email
        email_intent_analyzer_prompt = PromptTemplate(
            template=email_intent_analyzer_prompt_template,
            input_variables=["email"]
        )
        self.extract_email_intent = email_intent_analyzer_prompt | llm | JsonOutputParser()

        # extract interest from the email
        email_interest_level_analyzer_prompt = PromptTemplate(
            template=email_interest_level_analyzer_prompt_template,
            input_variables=["email"]
        )
        self.extract_email_interest = email_interest_level_analyzer_prompt | llm | JsonOutputParser()

        # extract emotion from the email
        email_emotion_analyzer_prompt = PromptTemplate(
            template=email_emotion_analyzer_prompt_template,
            input_variables=["email"]
        )
        self.extract_email_emotion = email_emotion_analyzer_prompt | llm | JsonOutputParser()

        # generate call subject from the email
        generate_call_subject_prompt = PromptTemplate(
            template=generate_call_subject_prompt_template,
            input_variables=["email"]
        )
        self.generate_call_subject = generate_call_subject_prompt | llm | JsonOutputParser()

        # generate call description from the email
        generate_call_description_prompt = PromptTemplate(
            template=generate_call_description_prompt_template,
            input_variables=["email"]
        )
        self.generate_call_description = generate_call_description_prompt | llm | JsonOutputParser()

        # categorize call purpose from the email
        categorize_call_prompt = PromptTemplate(
            template=categorize_call_prompt_template,
            input_variables=["email"]
        )
        self.extract_call_purpose = categorize_call_prompt | llm | JsonOutputParser()

        # extract date/time from the email
        extract_date_for_call_prompt= PromptTemplate(
            template=extract_date_for_call_prompt_template,
            input_variables=["email"]
        )
        self.extract_call_date_time = extract_date_for_call_prompt | llm | JsonOutputParser()

        # Categorize email chain
        category_prompt = PromptTemplate(
            template=categorize_email_prompt_template,
            input_variables=["email"]
        )
        self.categorize_email = category_prompt | llm | JsonOutputParser()

        # Used to design queries for RAG retrieval
        query_prompt = PromptTemplate(
            template=rag_query_prompt_template,
            input_variables=["email"]
        )
        self.design_rag_query = query_prompt | llm | JsonOutputParser()

        # Used to write a draft email based on category and related informations
        draft_prompt = PromptTemplate(
            template=draft_email_prompt_template,
            input_variables=["category", "email", "informations"]
        )
        self.write_draft_email = draft_prompt | llm | JsonOutputParser()

        # Verify the generated email
        verify_prompt = PromptTemplate(
            template=verify_email_prompt_template,
            input_variables=["category", "initial_email", "generated_email", "informations"]
        )
        self.verify_email = verify_prompt | llm | JsonOutputParser()

        # Qualifies the lead based on the email intent
        lead_qualifier_prompt = PromptTemplate(
            template=lead_qualifier_prompt_template,
            input_variables=["email"]
        )
        self.lead_qualify_status = lead_qualifier_prompt | llm | JsonOutputParser()
