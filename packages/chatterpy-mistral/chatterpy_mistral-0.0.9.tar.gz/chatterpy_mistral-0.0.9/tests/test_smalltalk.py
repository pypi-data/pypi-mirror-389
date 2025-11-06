# Unit tests for smallTalk function in ChatterPy module

from chatterpy_mistral.smalltalk import smallTalk, questions, comments

# Correct return type test  
def test_smallTalk_returns_string():
    actualQuestion = smallTalk(True)
    actualComment = smallTalk(False)
    
    assert isinstance(actualQuestion, str), f"Expected smallTalk(True) to return a string. It instead returned {actualQuestion}"
    assert isinstance(actualComment, str), f"Expected smallTalk(False) to return a string. It instead returned {actualComment}"

# Correct return (question or comment) based on input tests
def test_questions(): 
    actual = smallTalk(True)
    assert actual in questions, f"Expected a question from the questions list, got {actual}"

def test_comments(): 
    actual = smallTalk(False)
    assert actual in comments, f"Expected a question from the questions list, got {actual}"

# Sufficient coverage of questions/comments tests
def test_smallTalk_randomness_questions(): 
    chosen = set(smallTalk(True) for i in range(50))
    assert len(chosen) > 1

def test_smallTalk_randomness_comments(): 
    chosen = set(smallTalk(False) for i in range(50))
    assert len(chosen) > 1