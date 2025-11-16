import boto3
from botocore.exceptions import ClientError
import json

# Initialize AWS Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # Replace with your AWS region
)

# Initialize Bedrock Knowledge Base client
bedrock_kb = boto3.client(
    service_name='bedrock-agent-runtime',
    region_name='us-east-1'  # Replace with your AWS region
)


def valid_prompt(prompt: str, model_id: str) -> bool:
    """
    Validate the user's prompt by classifying it into one of several categories.
    Only prompts classified as Category E (heavy machinery) are allowed.

    Returns:
        True  -> prompt is valid
        False -> prompt is invalid
    """

    classification_prompt = f"""
    Human: Classify the provided user request into ONE of the following categories.

    Category A: The request is asking about how the LLM model works or system architecture.
    Category B: The request uses profanity, toxic intent, or harmful wording.
    Category C: The request is about any subject NOT related to heavy machinery.
    Category D: The request is asking about instructions, system behavior, or meta-questions.
    Category E: The request is ONLY related to heavy machinery topics.

    <user_request>
    {prompt}
    </user_request>

    Respond ONLY with the category letter (Example: "Category C").

    Assistant:
    """

    try:
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": classification_prompt}]
            }
        ]

        response = bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "max_tokens": 10,
                "temperature": 0,
                "top_p": 0.1,
            })
        )

        result_text = json.loads(response["body"].read())["content"][0]["text"]
        cleaned = result_text.lower().strip()

        print(f"[Prompt Classification] {cleaned}")

        return cleaned == "category e"

    except ClientError as e:
        print(f"Error validating prompt: {e}")
        return False


def query_knowledge_base(query, kb_id):
    """
    Query the Bedrock Knowledge Base and return results with source metadata.

    Returns:
        list: List of dicts containing 'content', 'score', and 'source' information
    """
    try:
        response = bedrock_kb.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )

        # Extract and enrich results with source information
        enriched_results = []
        for result in response['retrievalResults']:
            enriched_result = {
                'content': result['content']['text'],
                'score': result.get('score', 0),
                'source': {
                    'type': result['location']['type'],
                    's3_uri': result['location'].get('s3Location', {}).get('uri', 'Unknown'),
                    'metadata': result.get('metadata', {})
                }
            }
            enriched_results.append(enriched_result)

        return enriched_results
    except ClientError as e:
        print(f"Error querying Knowledge Base: {e}")
        return []


def generate_response(prompt, model_id, temperature, top_p):
    try:

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        response = bedrock.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "max_tokens": 500,
                "temperature": temperature,
                "top_p": top_p,
            })
        )
        return json.loads(response['body'].read())['content'][0]["text"]
    except ClientError as e:
        print(f"Error generating response: {e}")
        return ""
