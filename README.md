# Question Answering with Info Retrieval

This app allows you to interact with an NLP model which automatically answers
questions. If a SerpAPI key is provided when runnning the streamlit script,
then questions can be asked without providing the title of a Wikipedia article
(which would hopefully have the answer to the question). Regardless of whether
a SerpAPI key is provided, a Wikipedia article can be obtained by the title,
and then the NLP pipeline will look to answer the question using that article.

If a SerpAPI key is provided, and the user selects to use SerpAPI to find
the best Wikipedia article, then the query is inputted to Google using
SerpAPI, which will return the title most relevant Wikipedia article. 
Whether the article title is obtained through the user or SerpAPI, the
script then uses the Wikimedia API to get the article text (the Wikimedia
API has much more generous rate limits than SerpAPI). Then the NLP pipeline 
parses the document to answer your question.

Regardless of whether a SerpAPI key is provided, every query is compared 
with a cache of previous queries. If the current query is sufficiently similar
to a cached query, then the NLP pipeline parses the article corresponding to
the cached query (the article's title is also cached). If a query is not
sufficiently similar to a cached query, and the article title was not
provided by the user, then that query and its article title are cached.

The pipeline parses the Wikipedia article in paragraph chunks. Unless 
the answer to the given question is found at the end of the Wikipedia 
article, this is typically much faster than inputting the entire document.
If an answer has a confidence surpassing some specified value, that answer
is returned; if there is no such confident answer, the most confident answer
is returned.

Part-of-speech tagging could be used to approximate the question's subject 
(insofar as what the corresponding Wiki  article might be titled), but once 
a question contains more than 1 subject or object, it is possible the 
wrong Wiki article(s) will be retrieved, which would probably result in 
a fruitless and lengthy query.

Note: unless the user wants to provide the title of the article to parse,
the article title input box should read 'SerpAPI'. Also, when running in 
command line, pass args to streamlit.py without flags. E.g., if passing 
SerpAPI token 'test_token' to streamlit.py, the command will be:

> streamlit run streamlit.py serp_api_key=test_token
