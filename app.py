import streamlit as st
import boto3
from botocore.exceptions import ClientError
import json
from bedrock_utils import query_knowledge_base, generate_response, valid_prompt


# Streamlit UI
st.title("Bedrock Chat Application")

# Sidebar for configurations
st.sidebar.header("Configuration")
model_id = st.sidebar.selectbox("Select LLM Model", [
                                "anthropic.claude-3-haiku-20240307-v1:0", "anthropic.claude-3-5-sonnet-20240620-v1:0"])
kb_id = st.sidebar.text_input("Knowledge Base ID", "your-knowledge-base-id")
temperature = st.sidebar.select_slider(
    "Temperature", [i/10 for i in range(0, 11)], 1)
top_p = st.sidebar.select_slider("Top_P", [i/1000 for i in range(0, 1001)], 1)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = []

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display sources if available for this message
        if message["role"] == "assistant" and idx < len(st.session_state.sources):
            sources = st.session_state.sources[idx]
            if sources:
                with st.expander("📚 View Sources", expanded=False):
                    st.markdown("### Information Retrieved From:")
                    for source_idx, result in enumerate(sources, 1):
                        st.markdown(
                            f"**Source {source_idx}** (Relevance: {result['score']:.2%})")

                        s3_uri = result['source']['s3_uri']
                        filename = s3_uri.split(
                            '/')[-1] if s3_uri != 'Unknown' else 'Unknown'

                        st.markdown(f"- **Document**: `{filename}`")
                        st.markdown(f"- **S3 Location**: `{s3_uri}`")

                        content_preview = result['content'][:200] + "..." if len(
                            result['content']) > 200 else result['content']
                        st.markdown(
                            f"- **Content Preview**: {content_preview}")

                        if result['source']['metadata']:
                            st.markdown(
                                f"- **Metadata**: {result['source']['metadata']}")

                        st.divider()

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if valid_prompt(prompt, model_id):
        # Query Knowledge Base
        kb_results = query_knowledge_base(prompt, kb_id)

        # DEBUG: Show number of results
        st.info(f"📊 Found {len(kb_results)} knowledge base results")

        # Prepare context from Knowledge Base results
        context = "\n".join([result['content'] for result in kb_results])

        # Generate response using LLM
        full_prompt = f"Context: {context}\n\nUser: {prompt}\n\n"
        response = generate_response(full_prompt, model_id, temperature, top_p)

        # Display assistant response with sources
        with st.chat_message("assistant"):
            st.markdown(response)

            # Display sources in an expandable section
            if kb_results:
                with st.expander("📚 View Sources", expanded=True):
                    st.markdown("### Information Retrieved From:")
                    for idx, result in enumerate(kb_results, 1):
                        st.markdown(
                            f"**Source {idx}** (Relevance: {result['score']:.2%})")

                        # Extract filename from S3 URI
                        s3_uri = result['source']['s3_uri']
                        filename = s3_uri.split(
                            '/')[-1] if s3_uri != 'Unknown' else 'Unknown'

                        st.markdown(f"- **Document**: `{filename}`")
                        st.markdown(f"- **S3 Location**: `{s3_uri}`")

                        # Show content preview
                        content_preview = result['content'][:200] + "..." if len(
                            result['content']) > 200 else result['content']
                        st.markdown(
                            f"- **Content Preview**: {content_preview}")

                        # Show metadata if available
                        if result['source']['metadata']:
                            st.markdown(
                                f"- **Metadata**: {result['source']['metadata']}")

                        st.divider()

        # Save to session state
        st.session_state.messages.append(
            {"role": "assistant", "content": response})
        st.session_state.sources.append(kb_results)
    else:
        response = "I'm unable to answer this, please try again"
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append(
            {"role": "assistant", "content": response})
        st.session_state.sources.append([])
