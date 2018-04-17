from nltk.sentiment.vader import SentimentIntensityAnalyzer

sid = SentimentIntensityAnalyzer()


#-----------------------------------------------------------------------------------------------------------------------
def getMaxPolarity(text):
    polarity_scores = sid.polarity_scores(text)
    polarity_scores.pop('compound')
    
    polarities = polarity_scores.keys()
    scores     = polarity_scores.values()

    return polarities[scores.index(max(scores))]


#-----------------------------------------------------------------------------------------------------------------------
def getPolarities(text):
    polarity_scores = sid.polarity_scores(text)
    polarity_scores.pop('compound')

    return polarity_scores


#-----------------------------------------------------------------------------------------------------------------------
def getIntensity(text):
    polarity_scores = sid.polarity_scores(text)
    return polarity_scores['compound']
