# app.py
from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=30)

# Quiz questions, correct answers, and explanations
quiz_data = [
    {
        "id": 1,
        "question": "Which CSS property is used to create a flexible box layout?",
        "options": ["display: block", "display: flex", "display: grid", "display: inline"],
        "correct": 1,  # 0-indexed, so 1 = "display: flex"
        "explanation": "The 'display: flex' property establishes a flex container, enabling a flex context for all its direct children."
    },
    {
        "id": 2,
        "question": "Which selector targets an element with the ID \"header\"?",
        "options": ["#header", ".header", "header", "*header"],
        "correct": 0,  # 0-indexed, so 0 = "#header"
        "explanation": "In CSS, the '#' symbol is used to select elements by their ID attribute."
    },
    {
        "id": 3,
        "question": "Which HTML5 element is used to define navigation links?",
        "options": ["<navigation>", "<menu>", "<nav>", "<links>"],
        "correct": 2,  # 0-indexed, so 2 = "<nav>"
        "explanation": "The <nav> element is a semantic HTML5 tag specifically designed for navigation sections."
    },
    {
        "id": 4,
        "question": "Which CSS property is used to create rounded corners?",
        "options": ["corner-radius", "round-corners", "border-radius", "border-corner"],
        "correct": 2,  # 0-indexed, so 2 = "border-radius"
        "explanation": "The 'border-radius' property allows you to create rounded corners on elements."
    },
    {
        "id": 5,
        "question": "Which attribute makes a form submit to a specific URL?",
        "options": ["url", "action", "method", "target"],
        "correct": 1,  # 0-indexed, so 1 = "action"
        "explanation": "The 'action' attribute specifies where to send the form data when submitted."
    },
    {
        "id": 6,
        "question": "What CSS unit is relative to the font-size of the element?",
        "options": ["px", "%", "em", "vh"],
        "correct": 2,  # 0-indexed, so 2 = "em"
        "explanation": "The 'em' unit is relative to the font-size of the element (e.g., 2em means 2 times the font size)."
    },
    {
        "id": 7,
        "question": "Which property specifies the spacing between lines of text?",
        "options": ["text-spacing", "line-height", "text-height", "line-spacing"],
        "correct": 1,  # 0-indexed, so 1 = "line-height"
        "explanation": "The 'line-height' property sets the height of a line box, controlling the spacing between lines of text."
    },
    {
        "id": 8,
        "question": "What is the correct way to add a comment in CSS?",
        "options": ["// This is a comment", "/* This is a comment */", "<!-- This is a comment -->", "# This is a comment"],
        "correct": 1,  # 0-indexed, so 1 = "/* This is a comment */"
        "explanation": "Comments in CSS are made with /* comment text */ syntax, allowing multi-line comments."
    },
    {
        "id": 9,
        "question": "Which HTML tag is used to define an unordered list?",
        "options": ["<ul>", "<ol>", "<list>", "<dl>"],
        "correct": 0,  # 0-indexed, so 0 = "<ul>"
        "explanation": "The <ul> (unordered list) tag is used to create a bulleted list in HTML."
    },
    {
        "id": 10,
        "question": "Which of these is a pseudo-class in CSS?",
        "options": [":before", ":hover", "::first-line", "::selection"],
        "correct": 1,  # 0-indexed, so 1 = ":hover"
        "explanation": "':hover' is a pseudo-class that selects elements when the mouse cursor is positioned over them. ':before' is actually a pseudo-element written as '::before' in CSS3, and '::first-line' and '::selection' are both pseudo-elements (note the double colons)."
    }
]

# Categories for feedback based on question numbers
skill_categories = {
    "CSS Selectors": [2, 10],
    "CSS Properties": [1, 4, 6, 7],
    "CSS Syntax": [8],
    "HTML Elements": [3, 9],
    "HTML Attributes": [5]
}

@app.route('/')
def index():
    session.clear()  # Clear any existing session data
    session['current_question'] = 0
    session['answers'] = {}
    return render_template('templates/index.html', question=quiz_data[0], quiz_data=quiz_data)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'current_question' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Store the current answer
        question_id = int(request.form.get('question_id'))
        answer = request.form.get(f'a{question_id}')
        
        if answer is not None:
            # Convert to zero-based index
            session['answers'][question_id] = int(answer.split('-')[1]) - 1
        
        # Move to next question or results
        next_question = request.form.get('next_question')
        if next_question == 'results':
            return redirect(url_for('results'))
        else:
            session['current_question'] = int(next_question) - 1
            return render_template('templates/index.html', 
                                  question=quiz_data[session['current_question']], 
                                  quiz_data=quiz_data,
                                  answers=session['answers'])
    
    # GET request - show current question
    return render_template('templates/index.html', 
                          question=quiz_data[session['current_question']], 
                          quiz_data=quiz_data,
                          answers=session.get('answers', {}))

@app.route('/results')
def results():
    if 'answers' not in session:
        return redirect(url_for('index'))
    
    answers = session['answers']
    
    # Calculate score
    correct_count = 0
    incorrect_questions = []
    
    for q in quiz_data:
        question_id = q['id']
        if question_id in answers and answers[question_id] == q['correct']:
            correct_count += 1
        else:
            incorrect_questions.append(question_id)
    
    score = f"{correct_count}/{len(quiz_data)}"
    
    # Generate AI feedback based on incorrect questions
    weak_categories = {}
    for category, question_ids in skill_categories.items():
        wrong_in_category = [q for q in incorrect_questions if q in question_ids]
        if wrong_in_category:
            weak_categories[category] = len(wrong_in_category) / len(question_ids)
    
    # Sort categories by weakness level (highest percentage first)
    weak_areas = sorted(weak_categories.items(), key=lambda x: x[1], reverse=True)
    
    # Generate learning resources based on weak areas
    learning_resources = []
    if weak_areas:
        for category, _ in weak_areas[:3]:  # Top 3 weak areas
            if category == "CSS Selectors":
                learning_resources.append("Practice with CSS selectors on CSS Diner (flukeout.github.io)")
                learning_resources.append("Study the difference between pseudo-classes and pseudo-elements")
            elif category == "CSS Properties":
                learning_resources.append("Complete the CSS Grid tutorial on MDN Web Docs")
                learning_resources.append("Practice building responsive layouts with Flexbox")
            elif category == "CSS Syntax":
                learning_resources.append("Review CSS syntax fundamentals on W3Schools")
            elif category == "HTML Elements":
                learning_resources.append("Take the free HTML5 certification on W3Schools")
                learning_resources.append("Practice using semantic HTML elements correctly")
            elif category == "HTML Attributes":
                learning_resources.append("Study form attributes and their proper usage")
    
    # If they did well, provide advanced resources
    if correct_count >= 8:
        learning_resources.append("Explore advanced CSS techniques like CSS variables and animations")
        learning_resources.append("Study ARIA attributes for better web accessibility")
    
    return render_template('results.html', 
                          score=score,
                          correct_count=correct_count,
                          quiz_data=quiz_data,
                          answers=answers,
                          incorrect_questions=incorrect_questions,
                          weak_areas=[area[0] for area in weak_areas],
                          learning_resources=learning_resources)

@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '_main_':
    app.run(debug=True)