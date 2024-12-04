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

quiz_data = load_quiz_data()
random.shuffle(quiz_data)  # 문제 순서를 무작위로 섞음
wrong_answers = []  # 오답 문제를 저장할 리스트

def shuffle_choices_with_mapping(question):
    """보기를 무작위로 섞고 새로운 정답 인덱스를 반환합니다."""
        
    # 환경 변수 기반 시드 초기화
    random.seed(os.getenv('RANDOM_SEED', time.time()))
    choices = question['infoChoice']
    correct_answers = question['infoAnswer']

    # 보기와 인덱스를 함께 섞기 위해 (index, choice) 형태로 변환
    indexed_choices = list(enumerate(choices))
    random.shuffle(indexed_choices)  # 무작위로 섞기

    # 섞인 보기를 생성하고, 새로운 정답 인덱스를 계산
    shuffled_choices = [(chr(65 + i), choice) for i, (_, choice) in enumerate(indexed_choices)]
    new_correct_answers = [
        chr(65 + i) for i, (original_index, _) in enumerate(indexed_choices)
        if chr(65 + original_index) in correct_answers
    ]

    return shuffled_choices, new_correct_answers

@app.route("/", methods=["GET", "POST"])
def quiz():
    
    global quiz_data
    random.shuffle(quiz_data)  # 요청 시마다 퀴즈 데이터 섞기
    # URL에서 question_index 가져오기, 기본값은 0
    question_index = int(request.args.get("question_index", 0))
    result = request.args.get("result", "")

    if request.method == "POST":
        # 사용자가 제출한 답변 가져오기
        user_answers = request.form.getlist("answer")
        correct_answers = session.get(f"correct_answers_{question_index}", [])

        # 정답 여부 판단
        if sorted(user_answers) == sorted(correct_answers):
            result = "정답입니다!"
        else:
            result = f"오답입니다! 정답은 {', '.join(correct_answers)}입니다."
            if question_index not in wrong_answers:
                wrong_answers.append(question_index)  # 중복 방지

        # 리다이렉트로 결과 전달
        return redirect(url_for('quiz', question_index=question_index, result=result))

    # 모든 문제를 푼 경우 오답 문제로 이동
    if question_index >= len(quiz_data):
        if wrong_answers:
            question_index = wrong_answers.pop(0)  # 오답 문제로 이동
        else:
            return render_template("end.html")  # 모든 문제 완료 시 종료 화면

    # 첫 번째 요청 시에만 보기를 섞고 세션에 저장
    if not session.get(f"choices_{question_index}"):
        shuffled_choices, new_correct_answers = shuffle_choices_with_mapping(quiz_data[question_index])
        session[f"choices_{question_index}"] = shuffled_choices
        session[f"correct_answers_{question_index}"] = new_correct_answers
    else:
        shuffled_choices = session.get(f"choices_{question_index}")
        new_correct_answers = session.get(f"correct_answers_{question_index}")

    # 템플릿 렌더링
    return render_template(
        "quiz.html",
        choices=shuffled_choices,
        question=quiz_data[question_index],
        question_index=question_index,
        result=result,
        correct_answers=new_correct_answers,  # 새로운 정답 전달
        quiz_length=len(quiz_data) + len(wrong_answers)  # 총 질문 수 + 오답 수
    )

if __name__ == '__main__':
    app.run()
