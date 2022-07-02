from transformers import pipeline
from transformers import RobertaTokenizer, TFRobertaForQuestionAnswering
import re

def get_pipeline_from_huggingface(model_name):

    return pipeline(
        task='question-answering', model=model_name, tokenizer=model_name
    )

def get_pipeline_from_disk(model_dir):

    load_args = {''}

    tokenizer = RobertaTokenizer.from_pretrained(
        model_dir, local_files_only=True
    )

    model = TFRobertaForQuestionAnswering.from_pretrained(
        model_dir, local_files_only=True
    )

    return pipeline(
        'question-answering', model=model, tokenizer=tokenizer
    )

def parse_by_paragraph(query, wiki_text, pipeline, score_threshold):

    if wiki_text is None:
        return {'answer': 'None', 'score': 0}, 'UNSUCCESSFUL QUERY'

    # Remove headings and very short paragraphs
    text = re.sub('\n.{,100}\n', '', wiki_text) 

    # Split article into paragraphs
    paragraphs = text.split('\n')

    best_response = {'answer': 'NA', 'score': -1}
    best_paragraph = None

    for para in paragraphs:
        
        response = pipeline({'question': query, 'context': para})
        if best_response['score'] < response['score']:
            best_response = response
            best_paragraph = para

        if score_threshold < best_response['score']:
            return best_response, best_paragraph

    return best_response, best_paragraph
