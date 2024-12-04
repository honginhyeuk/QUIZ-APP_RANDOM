from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import random
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 세션 사용을 위해 필요

# JSON 파일 로드 함수
def load_quiz_data():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    json_path = os.path.join(base_dir, 'quiz_data_sap_fi.json')
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 글로벌 변수
original_quiz_data = load_quiz_data()

def shuffle_choices_with_mapping(question):
    """보기를 무작위로 섞고 새로운 정답 인덱스를 반환합니다."""
    choices = question['infoChoice']
    correct_answers = question['infoAnswer']

    indexed_choices = list(enumerate(choices))
    random.shuffle(indexed_choices)

    shuffled_choices = [(chr(65 + i), choice) for i, (_, choice) in enumerate(indexed_choices)]
    new_correct_answers = [
        chr(65 + i) for i, (original_index, _) in enumerate(indexed_choices)
        if chr(65 + original_index) in correct_answers
    ]

    return shuffled_choices, new_correct_answers

@app.route("/", methods=["GET", "POST"])
def quiz():
    if 'shuffled_indices' not in session:
        quiz_data = original_quiz_data.copy()
        session['shuffled_indices'] = random.sample(range(len(quiz_data)), len(quiz_data))

    shuffled_indices = session['shuffled_indices']
    question_index = int(request.args.get("question_index", 0))

    if question_index >= len(shuffled_indices):
        if wrong_answers:
            question_index = wrong_answers.pop(0)
        else:
            return render_template("end.html")

    actual_question_index = shuffled_indices[question_index]
    question = original_quiz_data[actual_question_index]

    if not session.get(f"choices_{question_index}"):
        shuffled_choices, new_correct_answers = shuffle_choices_with_mapping(question)
        session[f"question_{question_index}"] = question
        session[f"choices_{question_index}"] = shuffled_choices
        session[f"correct_answers_{question_index}"] = new_correct_answers
    else:
        question = session[f"question_{question_index}"]
        shuffled_choices = session[f"choices_{question_index}"]
        new_correct_answers = session[f"correct_answers_{question_index}"]

    result = request.args.get("result", "")

    if request.method == "POST":
        user_answers = request.form.getlist("answer")
        if sorted(user_answers) == sorted(new_correct_answers):
            result = "정답입니다!"
        else:
            result = f"오답입니다! 정답은 {', '.join(new_correct_answers)}입니다."
            if question_index not in wrong_answers:
                wrong_answers.append(question_index)

        return redirect(url_for('quiz', question_index=question_index, result=result))

    return render_template(
        "quiz.html",
        choices=shuffled_choices,
        question=question,
        question_index=question_index,
        result=result,
        quiz_length=len(shuffled_indices) + len(wrong_answers)
    )

if __name__ == '__main__':
    app.run()
