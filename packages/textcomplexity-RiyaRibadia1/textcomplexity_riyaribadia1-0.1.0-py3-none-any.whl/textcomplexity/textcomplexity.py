import re

def count_syllables(word):
    """Roughly count syllables in an English word."""
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False

    for char in word:
        if char in vowels:
            if not prev_was_vowel:
                count += 1
            prev_was_vowel = True
        else:
            prev_was_vowel = False

    # Remove silent 'e'
    if word.endswith("e"):
        count -= 1
    if count <= 0:
        count = 1
    return count


def get_complexity(text):
    """
    Compute basic text readability metrics.

    Parameters
    ----------
    text : str
        Input text string.

    Returns
    -------
    dict
        A dictionary containing:
        - flesch_score
        - flesch_kincaid
        - avg_sentence_length
        - complexity_label
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r'\w+', text)

    if not sentences or not words:
        return {"error": "Text too short for analysis."}

    syllables = sum(count_syllables(word) for word in words)
    num_words = len(words)
    num_sentences = len(sentences)

    # Flesch Reading Ease formula
    flesch_score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllables / num_words)

    # Flesch–Kincaid Grade Level formula
    flesch_kincaid = 0.39 * (num_words / num_sentences) + 11.8 * (syllables / num_words) - 15.59

    # Average sentence length
    avg_sentence_length = round(num_words / num_sentences, 2)

    # Assign complexity label
    if flesch_score >= 80:
        label = "Easy"
    elif flesch_score >= 50:
        label = "Moderate"
    else:
        label = "Hard"

    return {
        "flesch_score": round(flesch_score, 2),
        "flesch_kincaid": round(flesch_kincaid, 2),
        "avg_sentence_length": avg_sentence_length,
        "complexity": label,
    }


if __name__ == "__main__":
    sample = "Reinforcement learning enables agents to learn from trial and error."
    print(get_complexity(sample))
