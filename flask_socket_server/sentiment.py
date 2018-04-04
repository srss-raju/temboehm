from nltk.sentiment.vader import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()
scores = sid.polarity_scores(message_text)
testString = None
def getScore(message_text):
    print(message_text)
    scores = sid.polarity_scores(message_text)
    
    for key in sorted(scores):
        if scores['neu'] > scores['pos'] and scores['neu'] > scores['neg']:
            print("Neutral")
        elif scores['pos'] > scores['neu'] and scores['pos'] > scores['neg']:
            print("Positive")
        else:
            print("Negative")   
        break

    return testString
    #print('{0}: {1}, '.format(key, scores[key]), end='')