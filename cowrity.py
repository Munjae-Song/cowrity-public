import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import requests
import json
import anthropic # Anthropic API를 사용하기 위한 패키지
from google import genai # Google Gemini API를 사용하기 위한 패키지
from google.genai import types # Google Gemini API를 사용하기 위한 패키지
from openai import OpenAI # OpenAI API를 사용하기 위한 패키지


# 글로벌 API 키 설정
# 각 LLM에 사용하는 API-Key를 등록
CLAUDE_API_KEY = "Claude API-Key"
PERPLEXITY_API_KEY = "Perplexity API-Key"
GEMINI_API_KEY = "Gemini API-Key"
OPENAI_API_KEY = "OepnAI API-Key"  

# 글로벌 시스템 프롬프트 설정
# 각 요청에 따라 입력 되는 시스템 프롬프트.
SYSTEM_PROMPTS = {
    "request": """당신은 요청을 처리하는 AI 어시스턴트입니다. 주어진 요청에 대해 정확하고 신속하게 답변할 것. 영어질문에는 영어로, 한국어 질문에는 한국어로 답할것.
                  문체는 하다.이다 체로 작성. 일본어 번역체나 영어 번역체는 사용하지 말고 맞춤법을 지킬것. 
                  답변 마지막에는 ##### 표시를 하고 질문과 답변을 50단어로 요약해줘.""",
    "direct": """당신은 전문 전공 서적 수준의 답을 하는 AI 어시스턴트입니다. 영어질문에는 영어로, 한국어 질문에는 한국어로 답할것. 
                 문체는 하다.이다 체로 작성. 일본어 번역체나 영어 번역체는 사용하지 말고 맞춤법을 지킬것. 
                 답변 마지막에는 ##### 표시를 하고 질문과 답변을 50단어로 요약해줘.""",
    "refine": """당신은 전문 편집자입니다. 주어진 텍스트를 더 자연스럽고 읽기 쉽게 다듬을 것. 영어질문에는 영어로, 한국어 질문에는 한국어로 답할것. 
                 문체는 하다.이다 체로 작성. 일본어 번역체나 영어 번역체는 사용하지 말고 맞춤법을 지킬것. 
                 답변 마지막에는 ##### 표시를 하고 질문과 답변을 50단어로 요약해줘.""",
    "fact_check": """당신은 팩트체커입니다. 주어진 텍스트의 사실 관계를 검증하고 잘못된 정보가 있다면 정확한 정보로 수정할 것. 
                    영어질문에는 영어로, 한국어 질문에는 한국어로 답할것. 문체는 하다.이다 체로 작성. 
                    일본어 번역체나 영어 번역체는 사용하지 말고 맞춤법을 지킬것. 
                    팩트 체크는 다음과 같이 할 것
                    1. 사실인지 확인
                    2. 잘못된 정보가 있다면 정확한 정보로 수정
                    3. 가능한 한 출처나 근거 제시
                    4. 검증 불가능한 내용은 명시
                    답변 형식은 다음 3가지로 할 것 ✅ 사실 확인된 내용 ❌ 잘못된 정보 (정정: 올바른 정보) ⚠️ 검증 불가능하거나 주의 필요한 내용.
                    출처는 링크를 제시할 것.
                    답변 마지막에는 ##### 표시를 하고 질문과 답변을 50단어로 요약해줘.""",
    "refine_fact": """당신은 전문 편집자이자 팩트체커입니다. 주어진 텍스트를 더 자연스럽고 읽기 쉽게 다듬고 사실 관계도 검증할 것. 영어질문에는 영어로, 한국어 질문에는 한국어로 답할것. 
                    문체는 하다.이다 체로 작성. 일본어 번역체나 영어 번역체는 사용하지 말고 맞춤법을 지킬것. 
                    팩트 체크는 다음과 같이 할 것
                    1. 사실인지 확인
                    2. 잘못된 정보가 있다면 정확한 정보로 수정
                    3. 가능한 한 출처나 근거 제시
                    4. 검증 불가능한 내용은 명시
                    답변 형식은 다음 3가지로 할 것 ✅ 사실 확인된 내용 ❌ 잘못된 정보 (정정: 올바른 정보) ⚠️ 검증 불가능하거나 주의 필요한 내용.
                    출처는 링크를 제시할 것.
                    답변 마지막에는 ##### 표시를 하고 질문과 답변을 50단어로 요약해줘.""",
    "debate": """당신은 비판적으로 분석하는 토론 전문가입니다. 주어진 텍스트에 대해 논리적 모순이나 비약 등을 지적하고 다양한 시각으로 토론하고 건설적인 의견을 제시할 것. 
                 영어질문에는 영어로, 한국어 질문에는 한국어로 답할것. 문체는 하다.이다 체로 작성. 일본어 번역체나 영어 번역체는 사용하지 말고 맞춤법을 지킬것. 
                 답변 마지막에는 ##### 표시를 하고 질문과 답변을 50단어로 요약해줘."""
}

# 사용자 목적별 프롬프트 설정
PURPOSE_PROMPTS = {
    "writer": "작가의 관점에서 정돈 된 문장과 서사 구조를 중심으로 글을 작성한다.",
    "student": "학생의 관점에서 학술적인 접근을 기본으로, 개념을 명확히 하고 교육적 가치 중심으로 보고서를 작성한다.",
    "reporter": "기자의 관점에서 사실 확인과 객관적 분석에 중점을 두며, 뉴스 가치와 사회적 영향을 고려한 기사를 작성한다.",
    "officeworker": "회사원의 관점에서 실무적이고 효율적인 접근을 하며, 비즈니스 활용도와 실용성에 중점을 둔 보고서를 작성한다."
}

class CowrityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cowrity Ver. 0.1 - FactoryStat")
        self.root.geometry("1350x800+5+5")  # 윈도우 크기와 위치 (width x height + x + y)
        self.root.configure(bg='#f0f0f0')
        
        # 이전 내용 요약 저장 변수
        self.previous_summary = ""
        
        # 메인 프레임
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=3)
        
        # Row 0: 언어 모델 선택 드롭박스들
        model_frame = ttk.Frame(main_frame)
        model_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        model_frame.columnconfigure(0, weight=1)
        model_frame.columnconfigure(1, weight=1)
        model_frame.columnconfigure(2, weight=1)
        model_frame.columnconfigure(3, weight=1)  # 목적 설정 콤보박스를 위한 컬럼 추가
        
        # 언어 모델 옵션
        model_options = ["Claude Sonnet 4(일반)","Claude Opus4(정교함/비쌈)","Claude Haiku 3.5(단순,저가)","Perplexity Sonar(일반)", "Perplexity Sonar Pro(정교함, 비쌈)", "Gemini 2.5 Flash(일반)", "Gemini 2.5 Pro(정교함, 비쌈)", "GPT-4.1(일반)", "OpenAI o3(추론모델)"]
        
        # 1차 언어모델 선택
        ttk.Label(model_frame, text="1차 언어모델:").grid(row=0, column=0, sticky=tk.W, padx=80)
        self.model1_var = tk.StringVar(value="Claude Sonnet 4(일반)")
        self.model1_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model1_var,
            values=model_options,
            state="readonly",
            width=30
        )
        self.model1_combo.grid(row=1, column=0, padx=5, pady=5)
        
        # 2차 언어모델 선택
        ttk.Label(model_frame, text="2차 언어모델:").grid(row=0, column=1, sticky=tk.W, padx=80)
        self.model2_var = tk.StringVar(value="Perplexity Sonar Pro(정교함, 비쌈)")
        self.model2_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model2_var,
            values=model_options,
            state="readonly",
            width=30
        )
        self.model2_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # 3차 언어모델 선택
        ttk.Label(model_frame, text="3차 언어모델:").grid(row=0, column=2, sticky=tk.W, padx=80)
        self.model3_var = tk.StringVar(value="Gemini 2.5 Pro(정교함, 비쌈)")
        self.model3_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model3_var,
            values=model_options,
            state="readonly",
            width=30
        )
        self.model3_combo.grid(row=1, column=2, padx=5, pady=5)
        
        # 목적 설정 선택
        ttk.Label(model_frame, text="사용자 목적:").grid(row=0, column=3, sticky=tk.W, padx=80)
        purpose_options = ["writer", "student", "reporter", "officeworker"]
        self.purpose_var = tk.StringVar(value="writer")
        self.purpose_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.purpose_var,
            values=purpose_options,
            state="readonly",
            width=15
        )
        self.purpose_combo.grid(row=1, column=3, padx=5, pady=5)
        
        # Row 1: 입력 프롬프트 텍스트박스
        input_frame = ttk.LabelFrame(main_frame, text="입력 프롬프트", padding="5")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            height=15,
            width=80,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Row 2: 버튼들
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
        # 왼쪽 영역: 언어모델 1 버튼들
        left_button_frame = ttk.LabelFrame(button_frame, text="언어모델 1", padding="5")
        left_button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        self.send_model1_btn = ttk.Button(
            left_button_frame,
            text="프롬프트 전송",
            command=lambda: self.send_to_model(1, "request")
        )
        self.send_model1_btn.pack(side=tk.LEFT, padx=5)
        
        self.discuss_model1_btn = ttk.Button(
            left_button_frame,
            text="토론",
            command=lambda: self.process_with_model(1, "debate")
        )
        self.discuss_model1_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_input_btn = ttk.Button(
            left_button_frame,
            text="입력 클리어",
            command=self.clear_input
        )
        self.clear_input_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_summary_btn = ttk.Button(
            left_button_frame,
            text="이전요약 초기화",
            command=self.clear_previous_summary
        )
        self.clear_summary_btn.pack(side=tk.LEFT, padx=5)
        
        # 중간 영역: 언어모델 2 버튼들
        middle_button_frame = ttk.LabelFrame(button_frame, text="언어모델 2", padding="5")
        middle_button_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # 첫 번째 행 (3개 버튼)
        middle_row1_frame = ttk.Frame(middle_button_frame)
        middle_row1_frame.pack(fill=tk.X, pady=2)
        
        self.send_model2_btn = ttk.Button(
            middle_row1_frame,
            text="프롬프트 전송",
            command=lambda: self.send_to_model(2, "request")
        )
        self.send_model2_btn.pack(side=tk.LEFT, padx=2)
        
        self.refine_model2_btn = ttk.Button(
            middle_row1_frame,
            text="문장 다듬기",
            command=lambda: self.process_with_model(2, "refine")
        )
        self.refine_model2_btn.pack(side=tk.LEFT, padx=2)
        
        self.fact_check_model2_btn = ttk.Button(
            middle_row1_frame,
            text="팩트 체크",
            command=lambda: self.process_with_model(2, "fact_check")
        )
        self.fact_check_model2_btn.pack(side=tk.LEFT, padx=2)
        
        # 두 번째 행 (2개 버튼)
        middle_row2_frame = ttk.Frame(middle_button_frame)
        middle_row2_frame.pack(fill=tk.X, pady=2)
        
        self.refine_fact_model2_btn = ttk.Button(
            middle_row2_frame,
            text="문장 다듬기+팩트 체크",
            command=lambda: self.process_with_model(2, "refine_fact")
        )
        self.refine_fact_model2_btn.pack(side=tk.LEFT, padx=2)
        
        self.discuss_model2_btn = ttk.Button(
            middle_row2_frame,
            text="토론",
            command=lambda: self.process_with_model(2, "debate")
        )
        self.discuss_model2_btn.pack(side=tk.LEFT, padx=2)
        
        # 오른쪽 영역: 언어모델 3 버튼들
        right_button_frame = ttk.LabelFrame(button_frame, text="언어모델 3", padding="5")
        right_button_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        
        # 첫 번째 행 (3개 버튼)
        right_row1_frame = ttk.Frame(right_button_frame)
        right_row1_frame.pack(fill=tk.X, pady=2)
        
        self.send_model3_btn = ttk.Button(
            right_row1_frame,
            text="프롬프트 전송",
            command=lambda: self.send_to_model(3, "request")
        )
        self.send_model3_btn.pack(side=tk.LEFT, padx=2)
        
        self.refine_model3_btn = ttk.Button(
            right_row1_frame,
            text="문장 다듬기",
            command=lambda: self.process_with_model(3, "refine")
        )
        self.refine_model3_btn.pack(side=tk.LEFT, padx=2)
        
        self.fact_check_model3_btn = ttk.Button(
            right_row1_frame,
            text="팩트 체크",
            command=lambda: self.process_with_model(3, "fact_check")
        )
        self.fact_check_model3_btn.pack(side=tk.LEFT, padx=2)
        
        # 두 번째 행 (2개 버튼)
        right_row2_frame = ttk.Frame(right_button_frame)
        right_row2_frame.pack(fill=tk.X, pady=2)
        
        self.refine_fact_model3_btn = ttk.Button(
            right_row2_frame,
            text="문장 다듬기+팩트 체크",
            command=lambda: self.process_with_model(3, "refine_fact")
        )
        self.refine_fact_model3_btn.pack(side=tk.LEFT, padx=2)
        
        self.discuss_model3_btn = ttk.Button(
            right_row2_frame,
            text="토론",
            command=lambda: self.process_with_model(3, "debate")
        )
        self.discuss_model3_btn.pack(side=tk.LEFT, padx=2)
        
        # Row 3: 출력 프롬프트 텍스트박스
        output_frame = ttk.LabelFrame(main_frame, text="출력 프롬프트", padding="5")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=40,
            width=80,
            font=("Arial", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Row 4: 하단 정보 및 클리어 버튼
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        bottom_frame.columnconfigure(1, weight=1)
        
        # 출력 클리어 버튼
        self.clear_output_btn = ttk.Button(
            bottom_frame,
            text="출력 클리어",
            command=self.clear_output
        )
        self.clear_output_btn.pack(side=tk.LEFT, padx=5)
        
        # 클립보드 복사 버튼 (수동 복사용)
        self.copy_response_2input_btn = ttk.Button(
            bottom_frame,
            text="응답 입력창에 복사",
            command=self.copy_to_clipboard,
            state=tk.DISABLED
        )
        self.copy_response_2input_btn.pack(side=tk.LEFT, padx=5)
        
        # 상태 표시
        self.status_label = ttk.Label(bottom_frame, text="준비", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 이전 요약 상태 표시
        self.summary_status_label = ttk.Label(bottom_frame, text="이전요약: 없음", foreground="gray")
        self.summary_status_label.pack(side=tk.LEFT, padx=10)
        # 프로그레스 바
        self.progress = ttk.Progressbar(
            bottom_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side=tk.LEFT, padx=10)
        
        # 앱 정보
        info_frame = ttk.Frame(bottom_frame)
        info_frame.pack(side=tk.RIGHT)
        
        # App Info 버튼
        self.app_info_btn = ttk.Button(
            info_frame,
            text="App Info",
            command=self.show_app_info
        )
        self.app_info_btn.pack(side=tk.LEFT, padx=5)
        
        app_info_label = ttk.Label(
            info_frame,
            text="Cowrity Ver. 0.1",
            font=("Arial", 12, "bold"),
            foreground="blue"
        )
        app_info_label.pack(side=tk.LEFT, padx=10)
        
        company_label = ttk.Label(
            info_frame,
            text="FactoryStat",
            font=("Arial", 10),
            foreground="gray"
        )
        company_label.pack(side=tk.LEFT)
        
        # 키보드 이벤트 바인딩
        self.input_text.bind('<Control-Return>', lambda e: self.send_to_model(1))
        
        # 클립보드 저장용 변수
        self.last_claude_response = ""
        
        # 초기 포커스 설정
        self.input_text.focus_set()
    
    def clear_input(self):
        """입력 프롬프트 클리어"""
        self.input_text.delete(1.0, tk.END)
        self.input_text.focus_set()
    
    def clear_output(self):
        """출력 프롬프트 클리어"""
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state=tk.DISABLED)
        # 클립보드 버튼 비활성화
        self.copy_response_2input_btn.configure(state=tk.DISABLED)
        self.last_response = ""
    
    def clear_previous_summary(self):
        """이전 내용 요약 초기화"""
        self.previous_summary = ""
        self.summary_status_label.configure(text="이전요약: 없음", foreground="gray")
        messagebox.showinfo("초기화 완료", "이전 내용 요약이 초기화되었습니다.")
    
    def copy_to_clipboard(self):
        """응답을 클립보드로 복사 (수동)"""
        try:
            if self.last_response:
                # tkinter의 클립보드 기능 사용 (pyperclip 대신)
                self.root.clipboard_clear()
                self.root.clipboard_append(self.last_response)
                self.root.update()  # 클립보드 업데이트 확인
                
                # 입력 프롬프트 텍스트박스에도 복사
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(1.0, self.last_response)
                
                # 성공 메시지 표시
                messagebox.showinfo("복사 완료", "응답이 클립보드와 입력 프롬프트에 복사되었습니다.")
            else:
                messagebox.showwarning("복사 실패", "복사할 응답이 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"클립보드 복사 중 오류가 발생했습니다: {str(e)}")
    
    def auto_copy_to_clipboard(self, text):
        """Claude 응답을 자동으로 클립보드에 복사"""
        try:
            # 메인 스레드에서 실행되도록 예약
            self.root.after(0, self._perform_auto_copy, text)
        except Exception as e:
            print(f"자동 클립보드 복사 오류: {e}")
    
    def _perform_auto_copy(self, text):
        """실제 자동 클립보드 복사 실행 (메인 스레드용)"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # 클립보드 업데이트 확인
            
            # 상태 표시로 자동 복사 알림
            self.root.after(0, lambda: self.update_status("Claude 응답이 클립보드에 자동 복사됨", "blue", False))
            
            # 3초 후 상태를 다시 "준비"로 변경
            self.root.after(3000, lambda: self.update_status("준비", "green", False))
            
        except Exception as e:
            print(f"클립보드 복사 실행 오류: {e}")
    
    def get_selected_model(self, model_num):
        """선택된 모델 이름 반환"""
        if model_num == 1:
            return self.model1_var.get()
        elif model_num == 2:
            return self.model2_var.get()
        elif model_num == 3:
            return self.model3_var.get()

    def send_to_model(self, model_num, request_type="direct"):
        """선택된 모델에 프롬프트 내용을 전송"""
        prompt = self.input_text.get(1.0, tk.END).strip()
        
        if not prompt: # 프롬프트가 비어있는지 확인
            messagebox.showwarning("경고", "프롬프트를 입력해주세요.")
            return
        
        # arg로 들어온 모델 번호에 따라 선택된 모델 이름을 가져온다.
        selected_model = self.get_selected_model(model_num)
        
        # 선택된 모델 이름을 확인
        self.update_status(f"{selected_model}로 전송 중...", "orange", True)
        
        # 백그라운드에서 처리, 쓰레드를 이용해서 진행한다.
        thread = threading.Thread(
            target=self.process_model_request,
            args=(model_num, selected_model, prompt, request_type)
        )
        thread.daemon = True
        thread.start()
    
    def process_with_model(self, model_num, task_type):
        """언어모델로 특정 작업 수행"""
        # 출력 텍스트에서 마지막 응답 가져오기
        output_content = self.output_text.get(1.0, tk.END).strip()
        # 입력 텍스트에서 프롬프트 가져오기
        input_prompt = self.input_text.get(1.0, tk.END).strip()
        
        if not output_content:
            if not input_prompt:
                messagebox.showwarning("경고", "처리할 내용이 없습니다.")
                return
        
        # 프롬프트가 비어있지 않으면 전체 프롬프트를 생성
        if input_prompt:
            full_prompt = f"{input_prompt}\n\n"
        elif output_content:
            full_prompt += f"{output_content}\n\n"
        else:
            return

        selected_model = self.get_selected_model(model_num)
       
        self.update_status(f"{selected_model}로 {task_type} 중...", "orange", True)
        
        # 백그라운드에서 처리 쓰레드로 처리함
        thread = threading.Thread(
            target=self.process_model_request,
            args=(model_num, selected_model, full_prompt, task_type)
        )
        thread.daemon = True
        thread.start()
    
    #각 모델에 입력한 프롬프트를 전송해서 처리하게 한다. 
    def process_model_request(self, model_num, model_name, prompt, task_type):
        """모델 요청 처리"""
        #model_options = ["Claude Sonnet 4(일반)","Claude Opus4(정교함/비쌈)","Claude Haiku 3.5(단순,저가)","Perplexity Sonar(일반)", "Perplexity Sonar Pro(정교함, 비쌈)", "Gemini 2.5 Flash(일반)", "Gemini 2.5 Pro(정교함, 비쌈)", "GPT-4.1(일반)", "OpenAI o3(추론모델)"]
        try:
            # 선택된 PURPOSE_PROMPTS 가져오기
            selected_purpose = PURPOSE_PROMPTS.get(self.purpose_var.get(), PURPOSE_PROMPTS["writer"])
            
            # 모델별 실제 API 호출
            if model_name == "Claude Sonnet 4(일반)":
                response = self.claude_api(prompt, task_type, model_name, selected_purpose)
                # 오류 응답인지 확인
                is_error = response.startswith("❌")
                
                # 성공적인 응답이면 클립보드 버튼 활성화
                if not is_error:
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
            elif model_name == "Claude Opus4(정교함/비쌈)":
                response = self.claude_api(prompt, task_type, model_name, selected_purpose)
                # 오류 응답인지 확인
                is_error = response.startswith("❌")
                
                # 성공적인 응답이면 클립보드 버튼 활성화
                if not is_error:
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
            elif model_name == "Claude Haiku 3.5(단순,저가)":
                response = self.claude_api(prompt, task_type, model_name, selected_purpose)
                # 오류 응답인지 확인
                is_error = response.startswith("❌")
                # 성공적인 응답이면 클립보드 버튼 활성화
                if not is_error:
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
            elif model_name == "Perplexity Sonar(일반)":
                response = self.perplexity_api(prompt, task_type, model_name, selected_purpose)
                # 오류 응답인지 확인
                is_error = response.startswith("❌")
                if response != "":
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
            elif model_name == "Perplexity Sonar Pro(정교함, 비쌈)":
                response = self.perplexity_api(prompt, task_type, model_name, selected_purpose)
                # 오류 응답인지 확인
                is_error = response.startswith("❌")
                if response != "":
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
            elif model_name == "Gemini 2.5 Flash(일반)":
                response = self.gemini_api(prompt, task_type, model_name, selected_purpose)
                # 오류 응답인지 확인
                is_error = response.startswith("❌")
                #response가 비어 있지 않으면  클립보드 버튼 활성화
                if response != "":
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
                
            elif model_name == "Gemini 2.5 Pro(정교함, 비쌈)":
                response = self.gemini_api(prompt, task_type, model_name, selected_purpose)
                is_error = response.startswith("❌")
                if response != "":
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
            elif model_name == "GPT-4.1(일반)":
                response = self.openai_api(prompt, task_type, model_name, selected_purpose)
                is_error = response.startswith("❌")
                if not is_error:
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
                # 오류 응답인지 확인
               #
            elif model_name == "OpenAI o3(추론모델)":
                response = self.openai_api(prompt, task_type, model_name, selected_purpose)
                is_error = response.startswith("❌")
                if not is_error:
                    self.root.after(0, lambda: self.copy_response_2input_btn.configure(state=tk.NORMAL))
                # 오류 응답인지 확인
                #
            else:
                response = f"❌ 지원하지 않는 모델입니다: {model_name}"
                is_error = True
            
            # UI 업데이트
            self.root.after(0, self.update_output, model_num, model_name, prompt, response, task_type, is_error)
            
        except Exception as e:
            error_msg = f"❌ 시스템 오류가 발생했습니다: {str(e)}"
            self.root.after(0, self.update_output, model_num, model_name, prompt, error_msg, task_type, True)
    
    def claude_api(self, prompt, task_type="direct", model_name="Claude Sonnet 4(일반)", purpose_prompt=PURPOSE_PROMPTS["writer"]):
        """Claude Opus 4 언어 모델 처리 함수 (스트리밍 방식)"""
        try:
            # Claude API 설정 (글로벌 변수 사용)
            # Anthropic 클라이언트 초기화
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            
            # 글로벌 시스템 프롬프트 사용
            system_prompt = SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS["direct"])

            #모델 이름에 따라서 모델을 선택한다.
            if model_name == "Claude Opus 4(정교함/비쌈)":
                model_selected = "claude-opus-4-0" 
                max_tokens_4this = 20000
            elif model_name == "Claude Sonnet 4(일반)":
                model_selected = "claude-sonnet-4-0"
                max_tokens_4this = 8192
            elif model_name == "Claude Haiku 3.5(단순,저가)":
                model_selected = "claude-3-5-haiku-latest"
                max_tokens_4this = 8192


            # debate의 경우 사용자 목적별 프롬프트 추가
            if task_type == "debate":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt}"
            elif task_type == "request":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt}"
            elif task_type == "direct":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt}"
            elif task_type == "refine":
                # 문장 다듬기 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine']} {purpose_prompt}"
            elif task_type == "fact_check":
                # 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['fact_check']} {purpose_prompt}"
            elif task_type == "refine_fact":
                # 문장 다듬기 + 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine_fact']} {purpose_prompt}" 
            
            # 스트리밍을 위한 응답 텍스트 저장
            full_response = ""
            
            # Claude API 스트리밍 호출
            with client.messages.stream(
                model=model_selected,
                #claude-sonnet-4-20250514  max_tokens=8192
                #model="claude-3-5-haiku-20241022" max_tokens=8192
                max_tokens=max_tokens_4this,
                temperature=1,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    # 실시간으로 UI 업데이트 (선택사항)
                    #self.root.after(0, self.update_streaming_output, text)
            

            # 성공적인 응답 처리
            success_message = f"✅ {model_name} 응답 완료 (스트리밍)\n\n{full_response}"
            
            # ##### 이후 요약 내용 추출 및 저장
            if "#####" in full_response:
                summary_part = full_response.split("#####", 1)[1].strip()
                self.previous_summary = summary_part
                # UI에서 요약 상태 업데이트
                self.root.after(0, lambda: self.summary_status_label.configure(
                    text=f"이전요약: {summary_part[:30]}{'...' if len(summary_part) > 30 else ''}", 
                    foreground="blue"
                ))
            
            # 클립보드용 응답 저장 (순수 텍스트만)
            self.last_response = full_response
            
            # 자동으로 클립보드에 복사
            self.auto_copy_to_clipboard(full_response)
            
            return success_message
                
        except anthropic.APIConnectionError:
            error_msg = "❌ 네트워크 연결 오류: Claude API에 연결할 수 없습니다. 인터넷 연결을 확인해주세요."
            return error_msg
        except anthropic.RateLimitError:
            error_msg = "❌ API 사용량 한도 초과: 잠시 후 다시 시도해주세요."
            return error_msg
        except anthropic.APIError as e:
            error_msg = f"❌ Claude API 오류: {str(e)}"
            return error_msg
        except Exception as e:
            error_msg = f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}"
            return error_msg

    def perplexity_api(self, prompt, task_type="request", model_name="Perplexity Sonar(일반)", purpose_prompt=PURPOSE_PROMPTS["writer"]):
        """Perplexity API 호출 함수"""
        try:
            # Perplexity API 설정 (글로벌 변수 사용)
            # API 엔드포인트
            url = "https://api.perplexity.ai/chat/completions"
            
            # 글로벌 시스템 프롬프트 사용
            system_prompt = SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS[task_type])
            
            #모델 이름에 따라서 모델을 선택한다.
            if model_name == "Perplexity Sonar Pro(정교함, 비쌈)":
                model_selected = "sonar-pro"
            elif model_name == "Perplexity Sonar(일반)":
                model_selected = "sonar"

            # debate의 경우 사용자 목적별 프롬프트 추가
            if task_type == "debate":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt}"
            elif task_type == "request":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt}"
            elif task_type == "direct":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt}"
            elif task_type == "refine":
                # 문장 다듬기 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine']} {purpose_prompt}"
            elif task_type == "fact_check":
                # 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['fact_check']} {purpose_prompt}"
            elif task_type == "refine_fact":
                # 문장 다듬기 + 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine_fact']} {purpose_prompt}"
            else:
                # 다른 task_type들은 기본 PURPOSE_PROMPTS와 함께 적용
                system_prompt = f"{SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS['direct'])} {purpose_prompt}"
            
            # 요청 헤더
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            
            final_prompt = prompt
            # 스트리밍을 위한 응답 텍스트 저장
            full_response = ""
            
            # 요청 데이터
            data = {
                "model": model_selected,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": ["perplexity.ai"],
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "month",
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1
            }
            
            # API 요청
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # 응답 확인
            if response.status_code == 200:
                response_data = response.json()
                
                # 응답 텍스트 추출
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # 인용 정보 추출
                citations = response_data.get("citations", [])
                
                # 최종 응답 구성
                full_response = content
                
                # 인용 정보가 있으면 추가
                if citations:
                    full_response += "\n\n--- 참고 출처 ---\n"
                    for i, citation in enumerate(citations, 1):
                        full_response += f"{i}. {citation}\n"
                
                success_message = f"✅ Perplexity 팩트체크 완료\n\n{full_response}"
                #return success_message
                
            else:
                error_msg = f"❌ Perplexity API 오류 (Status: {response.status_code}): {response.text}"
                return error_msg

            #클립보드용 응답 저장 (순수 텍스트만)
            self.last_response = full_response
            
            # 자동으로 클립보드에 복사
            self.auto_copy_to_clipboard(full_response)
            
            return success_message
       
        except requests.exceptions.Timeout:
            error_msg = "❌ Perplexity API 타임아웃: 요청 시간이 초과되었습니다."
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "❌ 네트워크 연결 오류: Perplexity API에 연결할 수 없습니다."
            return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Perplexity API 요청 오류: {str(e)}"
            return error_msg
        except json.JSONDecodeError:
            error_msg = "❌ Perplexity API 응답 파싱 오류: 잘못된 JSON 형식입니다."
            return error_msg
        except Exception as e:
            error_msg = f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}"
            return error_msg
        
    def gemini_api(self, prompt, task_type="request", model_name="Gemini 2.5 Flash(일반)", purpose_prompt=PURPOSE_PROMPTS["writer"]):
        """Gemini API 호출 함수"""
        try:

            # 글로벌 시스템 프롬프트 사용
            system_prompt = SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS[task_type])
            
            #모델 이름에 따라서 모델을 선택한다.
            if model_name == "Gemini 2.5 Pro(정교함, 비쌈)":
                model_selected = "gemini-2.5-pro"
            elif model_name == "Gemini 2.5 Flash(일반)":
                model_selected = "gemini-2.5-flash"

            # debate의 경우 사용자 목적별 프롬프트 추가
            if task_type == "debate":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt}"
            elif task_type == "request":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt}"
            elif task_type == "direct":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt}"
            elif task_type == "refine":
                # 문장 다듬기 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine']} {purpose_prompt}"
            elif task_type == "fact_check":
                # 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['fact_check']} {purpose_prompt}"
            elif task_type == "refine_fact":
                # 문장 다듬기 + 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine_fact']} {purpose_prompt}" 

            final_prompt = prompt
            

            client = genai.Client(api_key=GEMINI_API_KEY)

            contents = [types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=final_prompt),
                    ],
                ),
            ]
            tools = [types.Tool(googleSearch=types.GoogleSearch(
                )),
            ]
            # Gemini API 호출
            generate_content_config = types.GenerateContentConfig(
                thinking_config = types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                tools=tools,
                response_mime_type="text/plain",
                system_instruction=[
                    types.Part.from_text(text=system_prompt),
                ],
            )

            full_response = ""
            for chunk in client.models.generate_content_stream(
                model=model_selected,
                contents=contents,
                config=generate_content_config,
            ):
                # 스트리밍 응답처리를 하지 않고 full_response에 저장한다. 
                
                if chunk.text:
                    text_chunk = chunk.text
                    full_response += text_chunk
                    # UI 업데이트 (실시간 스트리밍)
                    #self.root.after(0, self.update_streaming_output, text_chunk)
                    # 클립보드용 응답 저장 (순수 텍스트만)

            
            # 최종 응답 구성
            #full_response = text_chunk 
            success_message = f"✅ Gemini 응답 완료\n\n{full_response}"
            # 클립보드용 응답 저장 (순수 텍스트만)
            self.last_response = full_response   
            # 자동으로 클립보드에 복사
            self.auto_copy_to_clipboard(full_response)
            return success_message
        
        except genai.exceptions.ApiError as e:
            return error_msg    
        
    def openai_api(self, prompt, task_type="request", model_name="GPT-4.1(일반)", purpose_prompt=PURPOSE_PROMPTS["writer"]):
        """OpenAI API 호출 함수"""
        try:
            # OpenAI API 설정 (글로벌 변수 사용)
            #모델 이름에 따라서 모델을 선택한다.
            if model_name == "GPT-4.1(일반)":
                model_selected = "gpt-4-1106-preview"
            elif model_name == "OpenAI o3(추론모델)":
                model_selected = "o3-mini"

            # 글로벌 시스템 프롬프트 사용
            system_prompt = SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS[task_type])
            
            # debate의 경우 사용자 목적별 프롬프트 추가
            if task_type == "debate":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['debate']} {purpose_prompt}"
            elif task_type == "request":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['request']} {purpose_prompt}"
            elif task_type == "direct":
                # 이전 내용 요약이 있으면 추가
                if self.previous_summary:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt} 이전 내용 요약: {self.previous_summary}"
                else:
                    system_prompt = f"{SYSTEM_PROMPTS['direct']} {purpose_prompt}"
            elif task_type == "refine":
                # 문장 다듬기 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine']} {purpose_prompt}"
            elif task_type == "fact_check":
                # 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['fact_check']} {purpose_prompt}"
            elif task_type == "refine_fact":
                # 문장 다듬기 + 팩트 체크 프롬프트
                system_prompt = f"{SYSTEM_PROMPTS['refine_fact']} {purpose_prompt}" 
            
            final_prompt = prompt
            
            full_response = ""
            
            # OpenAI API 클라이언트 초기화
            openai = OpenAI(api_key=OPENAI_API_KEY)


            # OpenAI API 호출
            response = openai.responses.create(
                model=model_selected,
                input = [
                    {"role": "user", "content": final_prompt},
                    {"role": "system", "content": system_prompt}
                ]
            )

            # 응답 텍스트 추출
            content = response.output_text
            # 최종 응답 구성
            full_response = content
            success_message = f"✅ OpenAI 응답 완료\n\n{full_response}"
            # 클립보드용 응답 저장 (순수 텍스트만)
            self.last_response = full_response
            # 자동으로 클립보드에 복사
            self.auto_copy_to_clipboard(full_response)
            
            return success_message
        
        except openai.error.APIConnectionError:
            error_msg = "❌ 네트워크 연결 오류: OpenAI API에 연결할 수 없습니다. 인터넷 연결을 확인해주세요."
            return error_msg
        except openai.error.RateLimitError:
            error_msg = "❌ API 사용량 한도 초과: 잠시 후 다시 시도해주세요."
            return error_msg    
        



    def update_streaming_output(self, text_chunk):
        """스트리밍 텍스트 실시간 업데이트 (선택적 기능)"""
        try:
            self.output_text.configure(state=tk.NORMAL)
            self.output_text.insert(tk.END, text_chunk)
            self.output_text.see(tk.END)
            self.output_text.configure(state=tk.DISABLED)
        except Exception as e:
            print(f"스트리밍 업데이트 오류: {e}")

    
    
    def update_output(self, model_num, model_name, prompt, response, task_type, is_error=False):
        """출력 텍스트 업데이트"""
        self.output_text.configure(state=tk.NORMAL)
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 구분선 추가 (첫 번째 메시지가 아닌 경우)
        if self.output_text.get(1.0, tk.END).strip():
            self.output_text.insert(tk.END, "\n" + "="*80 + "\n\n")
        
        # 작업 정보 표시
        task_names = {
            "request": "프롬프트 직접 전송",
            "direct": "전문적인 응답",
            "refine": "문장 다듬기",
            "fact_check": "팩트 체크",
            "refine_fact": "문장 다듬기+팩트 체크",
            "debate": "토론"
        }
        
        self.output_text.insert(tk.END, f"[{current_time}] {model_num}차 모델({model_name}) - {task_names[task_type]}\n")
        self.output_text.insert(tk.END, "-" * 80 + "\n\n")
        
        if is_error:
            self.output_text.insert(tk.END, f"오류: {response}\n\n")
        else:
            self.output_text.insert(tk.END, f"{response}\n\n")
        
        self.output_text.insert(tk.END, "\n" + "="*80 + "\n\n")

        # 자동 스크롤
        self.output_text.see(tk.END)
        self.output_text.configure(state=tk.DISABLED)
        
        # 상태 복원
        self.update_status("준비", "green", False)

    def update_status(self, text, color, show_progress):
        """상태 업데이트"""
        self.status_label.configure(text=text, foreground=color)
        
        if show_progress:
            self.progress.start()
        else:
            self.progress.stop()

    
    def show_app_info(self):
        """앱 정보를 새 윈도우에 표시"""
        info_window = tk.Toplevel(self.root)
        info_window.title("Cowrity App Information")
        info_window.geometry("500x400")
        info_window.configure(bg='#f0f0f0')
        info_window.resizable(False, False)
        
        # 윈도우를 부모 창 중앙에 배치
        info_window.transient(self.root)
        info_window.grab_set()
        
        # 메인 프레임
        main_frame = ttk.Frame(info_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 앱 제목
        title_label = ttk.Label(
            main_frame,
            text="Cowrity Ver. 0.1",
            font=("Arial", 20, "bold"),
            foreground="blue"
        )
        title_label.pack(pady=10)
        
        # 회사명
        company_label = ttk.Label(
            main_frame,
            text="FactoryStat",
            font=("Arial", 14),
            foreground="gray"
        )
        company_label.pack(pady=5)
        
        # 구분선
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=20)
        
        # 앱 설명
        description_text = """
        Cowrity는 다중 AI 언어모델을 활용한 텍스트 처리 도구입니다.

        주요 기능:
        • Claude, Perplexity, Gemini 등 다양한 AI 모델 지원
        • 문장 다듬기 및 팩트 체크 기능
        • 사용자 목적별 맞춤형 토론 및 분석
        • 자동 클립보드 복사 기능

        연락처 : info@factorystat.com

        """
        
        description_label = ttk.Label(
            main_frame,
            text=description_text.strip(),
            font=("Arial", 10),
            justify=tk.LEFT,
            wraplength=450
        )
        description_label.pack(pady=10, anchor=tk.W)
        
        # 닫기 버튼
        close_btn = ttk.Button(
            main_frame,
            text="닫기",
            command=info_window.destroy
        )
        close_btn.pack(pady=20)

def main():
    root = tk.Tk()
    app = CowrityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()