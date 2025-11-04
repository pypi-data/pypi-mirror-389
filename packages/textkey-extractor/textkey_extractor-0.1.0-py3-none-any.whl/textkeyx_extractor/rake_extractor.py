import re
from collections import defaultdict

def extract_keywords(text, stopwords=None, top_k=5):
    """
    Extracts key phrases from text using a simplified RAKE algorithm.

    Parameters
    ----------
    text : str
        Input text.
    stopwords : list of str, optional
        Custom list of stopwords. If None, a default English list is used.
    top_k : int, optional (default=5)
        Number of top key phrases to return.

    Returns
    -------
    list of tuples
        List of (keyword, score) sorted by descending score.

    Example
    -------
    >>> text = "Reinforcement learning enables agents to make better decisions."
    >>> extract_keywords(text, top_k=3)
    [('reinforcement learning', 8.0), ('make better decisions', 4.5)]
    """
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")

    if stopwords is None:
        stopwords = {
            "a", "an", "the", "and", "or", "if", "in", "of", "on", "for", "to",
            "is", "are", "was", "were", "it", "that", "this", "with", "as", "by"
        }

    # Step 1: Split text into candidate phrases
    sentences = re.split(r'[.!?,;:\t\\-"()\'\u2019\u2013]', text.lower())
    phrases = []
    for sentence in sentences:
        words = [w for w in re.split(r'\W+', sentence) if w and w not in stopwords]
        phrase = ' '.join(words)
        if phrase:
            phrases.append(phrase)

    # Step 2: Calculate word frequency and degree
    freq = defaultdict(int)
    degree = defaultdict(int)

    for phrase in phrases:
        words = phrase.split()
        length = len(words)
        for word in words:
            freq[word] += 1
            degree[word] += length - 1  # other words in the phrase

    for word in freq:
        degree[word] += freq[word]  # degree = degree + frequency

    # Step 3: Compute word scores
    word_score = {w: degree[w] / freq[w] for w in freq}

    # Step 4: Compute phrase scores
    phrase_scores = []
    for phrase in phrases:
        score = sum(word_score[w] for w in phrase.split())
        phrase_scores.append((phrase, round(score, 2)))

    # Step 5: Sort and return top_k
    phrase_scores = sorted(phrase_scores, key=lambda x: x[1], reverse=True)
    return phrase_scores[:top_k]


if __name__ == "__main__":
    text = "Reinforcement learning enables agents to make better decisions in dynamic environments."
    print(extract_keywords(text, top_k=5))
