from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import random
from flask_session import Session  # 서버 측 세션 저장소

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config["SESSION_TYPE"] = "filesystem"  # 세션 데이터를 파일로 저장
app.config["SESSION_PERMANENT"] = False
Session(app)

# JSON 파일 로드 함수
def load_quiz_data():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    json_path = os.path.join(base_dir, 'quiz_data_sap_fi.json')
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)

quiz_data = load_quiz_data()

def shuffle_choices_with_mapping(question):
    choices = question.get('infoChoice', [])
    correct_answers = question.get('infoAnswer', [])
    
    if not choices or not isinstance(choices, list):
        raise ValueError("보기 데이터가 유효하지 않습니다.")
    if not correct_answers or not isinstance(correct_answers, list):
        raise ValueError("정답 데이터가 유효하지 않습니다.")

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

    
    if request.method == "POST":
    try:
        print("POST 요청 수신")
        print(f"폼 데이터: {request.form}")

        user_answers = request.form.getlist("answer")
        print(f"사용자 답변: {user_answers}")

        if sorted(user_answers) == sorted(new_correct_answers):
            result = "정답입니다!"
        else:
            result = f"오답입니다! 정답은 {', '.join(new_correct_answers)}입니다."
        
        print(f"결과: {result}")
        return redirect(url_for('quiz', question_index=question_index + 1, result=result))
    except Exception as e:
        print(f"POST 처리 중 오류 발생: {e}")
        return redirect(url_for('quiz', question_index=question_index, result="오류가 발생했습니다."))


    
    if "shuffled_indices" not in session:
        session["shuffled_indices"] = random.sample(range(len(quiz_data)), len(quiz_data))

    shuffled_indices = session["shuffled_indices"]
    question_index = int(request.args.get("question_index", 0))

    # question_index 유효성 검사
    if question_index < 0 or question_index >= len(shuffled_indices):
        return redirect(url_for('quiz', question_index=0, result="유효하지 않은 질문 번호입니다."))

    actual_question_index = shuffled_indices[question_index]
    question = quiz_data[actual_question_index]

    if f"choices_{question_index}" not in session:
        shuffled_choices, new_correct_answers = shuffle_choices_with_mapping(question)
        session[f"choices_{question_index}"] = shuffled_choices
        session[f"correct_answers_{question_index}"] = new_correct_answers
    else:
        shuffled_choices = session[f"choices_{question_index}"]
        new_correct_answers = session[f"correct_answers_{question_index}"]

    result = request.args.get("result", "")

    if request.method == "POST":
        user_answers = request.form.getlist("answer") or []
        
        if not new_correct_answers:
            return redirect(url_for('quiz', question_index=question_index, result="오류가 발생했습니다."))

        if sorted(user_answers) == sorted(new_correct_answers):
            result = "정답입니다!"
        else:
            result = f"오답입니다! 정답은 {', '.join(new_correct_answers)}입니다."

        return redirect(url_for('quiz', question_index=question_index + 1, result=result))

    return render_template(
        "quiz.html",
        choices=shuffled_choices,
        question=question,
        question_index=question_index,
        result=result,
        quiz_length=len(shuffled_indices)
    )

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
