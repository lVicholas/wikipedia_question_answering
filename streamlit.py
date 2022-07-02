from logging import PlaceHolder
from absl import flags, app
import os
import streamlit as st
import re
from string import punctuation
import json

import pipeline_utils
from WikiArticleRetriever import WikiArticleRetriever

flags.DEFINE_string(
    'disk_model_dir', 
    None, 
    'directory containing pretrained transformer model and tokenizer'
)
flags.DEFINE_string(
    'huggingface_model_name',
    'deepset/roberta-base-squad2',
    'name of model to load from huggingface'
)
flags.DEFINE_integer(
    'query_max_char_len',
    386, # Maximum query length for huggingface/deepset/roberta-base-squad2
    'maximum length of a query in characters'
)
flags.DEFINE_string(
    'serp_api_key',
    None,
    'Key for accessing SerpAPI'
)
flags.DEFINE_float(
    'answer_score_threshold',
    .80,
    'answer confidence threshold which triggers automatic stopping'
)
FLAGS = flags.FLAGS

def main(unused_args):
    
    if FLAGS.serp_api_key is not None: # Use SerpAPI key if given
        serp_api_key = FLAGS.serp_api_key
    elif 'SERP_API_KEY' in os.environ.keys(): # Use SerpAPI key in environment
        serp_api_key = os.environ['SERP_API_KEY']
    else:
        st.warning(
            'No API key for SERP was provided or found.\n'
            'App can only use articles of cached article titles.'
        )

    # Open README.md
    with open(os.path.join(os.getcwd(), 'README.md')) as f:
        readme_txt = f.read()

    # Display README.MD
    with st.container():
        st.title('Wikipedia Answering Bot')

        for para in readme_txt.split('\n\n'):
            st.markdown(para)

    # Streamlit's session state allows saving variables over sessions
    # The following avoids reloading the model when queries change

    # If the pipeline has not yet been loaded... 
    if 'pipeline' not in st.session_state:

        # If loading pipeline from disk_model_dir
        if FLAGS.disk_model_dir is not None:
            model_location = FLAGS.disk_model_dir
            loading_str = f'Loading model from disk at\n{model_location}...'
            pipeline_load_args = {'model_dir': model_location}

        else: # Otherwise, download model from huggingface
            model_location = f'huggingface/{FLAGS.huggingface_model_name}'
            loading_str = f'Loading model from {model_location}...'
            pipeline_load_args = {'model_name': FLAGS.huggingface_model_name}

        # Spinner while model is loading
        with st.spinner(loading_str):
            pipeline = pipeline_utils.get_pipeline_from_huggingface(
                **pipeline_load_args
            )

        st.session_state.pipeline = pipeline # Save model
        st.session_state.success_str = f'Model from {model_location} is ready'
        st.success(st.session_state.success_str)

        with open('query_title_cache.txt', 'r', encoding='utf-8') as f:
            st.session_state.cached_a_titles = list(json.load(f).values())

    else: # If pipeline is already loaded and stored in session state
        pipeline = st.session_state.pipeline
        st.success(st.session_state.success_str)
        
    # Box for question input
    query = st.text_input(
        label='Input question',
        value='When did Kurt Godel die?',
        max_chars=FLAGS.query_max_char_len # Maximum char len of query
    )

    ANY_ARTICLE_OPTION = 'SerpAPI'

    selected_article = st.text_input(
        label='Article to parse for answer',
        value=ANY_ARTICLE_OPTION,
        placeholder=ANY_ARTICLE_OPTION
    )

    # Get title of most relevant Wikipedia article
    wiki_article_retriever = WikiArticleRetriever(serp_api_key)

    if selected_article == ANY_ARTICLE_OPTION.strip():
        
        # Get that articles text
        a_text, a_title = wiki_article_retriever.get_wiki_article(query)

    else:

        a_title = selected_article # Get text from selected article title
        a_text = wiki_article_retriever.get_wiki_article_from_title(a_title)

    if a_text is None and st.button('Begin query'):
        st.warning(
            'The query did not result in an article'
            ' likely to answer the question.'
        )

    elif st.button('Begin query'):
        with st.container():
            st.title('Query Results')

            st.text(f'Question: {query}')
            st.text(f'Retrieved article titled: {a_title}')

            with st.spinner('Parsing article for answer...'):
                response, paragraph = pipeline_utils.parse_by_paragraph(
                    query, a_text, pipeline, FLAGS.answer_score_threshold
                )

            # Streamlit markdown uses $ for Latex, so they have to be removed
            paragraph = re.sub('\$', 'USD ', paragraph)

            # Strip leading / trailing punctuation and get answer index bounds
            answer = response['answer'].strip(punctuation)
            answer_start = paragraph.index(answer)
            answer_end = answer_start + len(answer)

            # Markdown string for showing answer within paragraph
            context_markdown = (
                paragraph[:answer_start] 
                + '**__' 
                + answer
                + '__**'
                + paragraph[answer_end:]
            )

            # Display answer, its score, and containing paragraph
            st.text(
                f'Retrieved answer: {answer}'
                f' --- score: {round(response["score"], 3)}'
            )
            st.markdown(context_markdown)        


if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
