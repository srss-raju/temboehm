from nltk.sentiment.vader import SentimentIntensityAnalyzer

sid = SentimentIntensityAnalyzer()

def getPolarity(message_text):
    polarity_scores = sid.polarity_scores(message_text)
    print polarity_scores
    
    # return polarity_scores.['compound']

    polarity_scores.pop('compound')
    
    polarities = polarity_scores.keys()
    scores     = polarity_scores.values()

    return polarities[scores.index(max(scores))]
