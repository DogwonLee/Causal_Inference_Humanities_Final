# 인문학 데이터를 위한 인과추론 파이프라인
### "국제연맹의 방관은 신뢰 추락을 *유발*했는가?" — *Evening Star*, 1920년 6월 17일

**과목:** Causal Inference and AI — *인문학 데이터의 관계 분석*
**교재:** Judea Pearl & Dana Mackenzie, *The Book of Why* (2018)
**트랙:** B(자유 설계), 전부 Python으로 구현 — Step 3 옵션 B, Step 4 옵션 B/C, Step 6 옵션 A/C.

> *English version: [README_en.md](README_en.md)*

이 저장소는 하루치 신문을 원본 OCR에서 인과 모델, 나아가 인과추론까지 6단계로 운반하며, 과제의 핵심을 수행한다: **행위자가 주장한 인과와, 모델·증거로 실제 식별 가능한 인과를 분리하는 것.**

---

## 한눈에 (TL;DR)

1920년 신문 기사 하나는 국제연맹 이사회가 페르시아 방어를 연기했다고 보도하고, 영국 언론은 곧바로 연맹이 "신뢰를 잃었다", "이미 죽었다"고 단언했다. 이는 **2단(개입)** 의 확신에 찬 인과 주장(*방관 → 연맹의 죽음*)이면서 **1단(연관) 증거는 전혀 없다.** 모든 주장을 근거가 연결된 명시적 DAG에 밀어넣으면, 그 주장된 효과가 **식별되지 않음**이 드러난다. 유일한 뒷문 경로 `T ← U → O`가 기사가 결코 측정하지 않은 교란요인(1차대전 직후 강대국 정치)을 통과하기 때문이다. 우생학 예제와 똑같은 간극을, 다른 세기에서 확인한다.

---

## 실행 방법

```bash
pip install -r requirements.txt
python run_pipeline.py          # 6단계 전체를 끝까지 실행
```
각 단계는 `src/` 아래 독립 모듈로도 실행할 수 있다(예: `python src/causal_model.py`).
전부 **오프라인·규칙 기반**이라 API 키가 필요 없고 완전히 재현 가능하다.

## 저장소 구성

```
data/1920-06-17.txt        원본 OCR (Evening Star, LCCN sn83045462)
src/clean_newspapers.py    Step 2  정제 + 분할
src/extract_ekg.py         Step 3  엔티티 / 사건 / 인과 주장 추출
src/build_graph.py         Step 4  networkx 속성 그래프 -> CSV + GraphML
src/causal_model.py        Step 5  DAG, 주장 vs 분석가 간선, 뒷문 탐색
src/inference.py           Step 6  모티프 리더보드, 모순, 평결
src/confounding_demo.py    Step 6  정량 뒷문 시연 (보정 전 vs 보정 후)
run_pipeline.py            오케스트레이터
notebook.ipynb             동일 파이프라인을 셀 단위로 서술
outputs/                   nodes.csv, edges.csv, ekg.graphml, 레코드, 평결
figures/causal_dag.png     인과 다이어그램 (그림 1, 한글판: causal_dag_ko.png)
report.docx / report_ko.docx   서식 보고서(영/한)
```

---

# 보고서

## 0. 인과 질문

> **국제연맹의 페르시아 호소(1920년 6월)에 대한 *방관*은 연맹 신뢰의 붕괴** — 영국 언론이 "신뢰를 잃었다", "이미 죽었다"고 내린 평결 — 를 *유발*했는가?

분석 단위는 기사 한 편, *"Leagues' Inaction in Persia's Plea Given Criticism"* 이며 시간·장소 메타데이터(`워싱턴 D.C., 1920-06-17`; 런던·테헤란·모스크바발 통신)를 붙였다. 시간 순서가 중요하다 — 이사회 결정이 언론 평결보다 하루 앞서며, 그것이 바로 인과적 해석을 유혹한다.

## 1. 자료 수집과 선정 (Step 1)

출처는 미국 의회도서관 *Chronicling America*의 *Evening Star* 1920년 6월 17일 OCR(LCCN `sn83045462`) — 28,060행, 32면, 약 865 KB. 예제의 1925년 호와 다른 제목·날짜를 택한 이유는 이 호가 명시적 인과 표현으로 가득하기 때문이다("because" 37회, "led to" 19회 등). Step 6의 담론 분석을 위해 신문 전체를 말뭉치로 두고, 집중 인과 모델은 기사 한 편으로 좁혔다(트랙 B / 옵션 C).

## 2. 정제와 정규화 (Step 2)

`clean_newspapers.py`는 규칙 기반이며 **모든 변환을 로그**(`outputs/clean_log.txt`)로 남긴다:

- `===== PAGE n =====` 마커와 러닝 헤더 제거;
- 줄 끝 단어 끊김 복원 — 명시적 하이픈은 공백 없이 결합; 긴 소문자 조각 + 짧은 소문자 꼬리가 줄바꿈을 가로지르면 한 단어로 결합; 그 외 단일 줄바꿈은 공백으로 바꿔 실제 단어 경계(`men / who`)를 `menwho`로 융합하지 않고 보존;
- 공백·인코딩 정규화와 반복 OCR 오류의 소규모 치환;
- ALL-CAPS 헤드라인 줄을 앵커로 **585개 기사 조각**으로 분할.

1920년대 OCR은 신뢰할 만한 기사 경계가 없어 분할이 본질적으로 불완전하다. 휴리스틱을 일부러 단순하게 두고 조각 수를 로그로 남겨 잡음을 *드러냈다*. LLM 정제(옵션 B)는 인과 주장을 조용히 바꿀 환각성 '교정'을 피하려 채택하지 않았다.

## 3. 엔티티·사건·인과 주장 추출 (Step 3)

`extract_ekg.py`는 투명한 고전 NLP 방식(옵션 B)이다 — 모든 레코드가 감사 가능해야 하므로 LLM 대신 규칙 기반을 택했다.

- **개체명 인식(NER):** 대문자 다중 토큰 스팬을 불용어로 거르고 가제티어 단서로 유형화(Senator/Professor → 인물, 조직 단서어 → 조직, 지명 가제티어 → 장소).
- **인과 주장:** 인과 신호 어휘집("because", "led to", "in order to", "the cause of" …). 각 신호는 방향·관계유형·극성·신뢰도 대용값을 갖는다.
- 모든 주장은 **구체화(reify)** 되어 `CausalAssertion` 노드에 `CAUSE`, `EFFECT`, `EVIDENCE`(정확한 문장), `DERIVED_FROM` 간선이 붙는다 — 어떤 주장이든 원문 인용으로 되짚을 수 있다.

결과: **인과 주장 83개**, 인물 멘션 4,747, 조직 212, 장소 100, 개념 160. (재현율·정밀도는 LLM보다 낮지만, 그 대가로 완전한 투명성과 재현성을 얻는다 — 핵심이 '주장 감사'인 이상 옳은 선택이다.)

## 4. 지식그래프 구축 (Step 4)

`build_graph.py`는 레코드를 **networkx** `MultiDiGraph`(옵션 B)로 적재하고 `nodes.csv` / `edges.csv`(옵션 C)와 `ekg.graphml`(Gephi·yEd·Neo4j import 가능)로 내보낸다. 출처가 1급 시민이다: 모든 노드는 `DERIVED_FROM`으로 `Source`에, 모든 주장은 `EVIDENCE` 멘션에 연결된다. 합계: **노드 5,971, 간선 6,824.**

## 5. 인과 모델 구축 (Step 5)

`causal_model.py`는 기사의 *주장된* 인과 내용을 5개 변수 DAG로 옮기고 **원문이 빠뜨린 교란요인을 추가**한다. `figures/causal_dag.png`(**그림 1**, 한글판 `causal_dag_ko.png`) 참고.

| 변수 | 의미 | 역할 |
|----|----------------------------------------------|------|
| **T** | 페르시아 호소에 대한 연맹의 **방관** | 처치(treatment) |
| **O** | 연맹의 **신뢰**("죽었는가?") | 결과(outcome) |
| **M** | "첫 실전 시험" 실패 인식 | 매개(mediator) |
| **N** | 테헤란–모스크바 협상 진행 | 연기의 밝힌 이유 |
| **U** | 1차대전 직후 강대국·제국주의 정치 | **관측되지 않은 교란요인** |

**텍스트가 주장한 간선**(파란 실선):

* `T → O` — Times: *"Malice was the cause of discredit being brought upon the league."*
* `T → M → O` — 지지자들은 행동을 *"first practical test of its power to settle international disputes"* 로 기대했고, 실패하는 것은 *"one way of killing the league."*
* `N → T` — 이사회는 *"in order to give every opportunity for success of the exchanges … between Teheran and Moscow"* 위해 연기.

**분석가가 추가한 간선**(주황 점선):

* `U → T` — 강대국은 개입을 *줄이려* 했고(Bonar Law 하원 발언: *"endeavoring to reduce its commitments"*), 이것이 방관을 추동.
* `U → O` — 바로 그 제국주의적 성격을 비판자들이 정당성 깎기에 동원(Herald: *"militarists and imperialists"*).

따라서 `U`는 처치와 결과의 **공통 원인**으로 뒷문 경로를 연다. `M`은 `T → O` 경로 위의 **매개**일 뿐 교란요인이 아니며, 코드가 둘을 구분하고 DAG의 비순환성을 검증한다.

## 6. 인과추론 수행 (Step 6)

`inference.py`는 그래프 질의로 1·2단에서 논증한다:

* **인과 모티프 리더보드**(`motif_leaderboard.csv`): 솔직히 이 호의 담론은 상업적 인과(배송 지연이 판매를 "유발")가 지배하고, 정치적 모티프(*"… → 연맹에 가해진 불신"*)는 광고 잡음 아래에 떠오른다 — 1920년 신문 인과 언어가 대체로 무엇을 위한 것인지를 보여주는 발견이기도 하다.
* **모순·증거밀도**(`contradictions.csv`, `evidence_density.csv`).
* **뒷문 분석**(`causal_model.py`): 손수 구현한 d-분리 검사로 `T`와 `O` 사이 뒷문 경로를 열거. 정확히 하나, `T ← U → O`이며 **최소 보정집합은 `{U}`.**

**평결 — 세 가지를 구분하기:**

* *상관*: 방관과 불신이 (하루 차로) 함께 나타난다.
* *주장된 인과*: 행위자들은 방관이 불신을 **유발**했다고 확신한다(순수 2단 언어).
* *식별된 효과*: **없음.** `T → O` 식별엔 `U` 보정이 필요하나 원문이 이를 빠뜨린다 — Herald는 `U → O`를 직접 단언하고 Bonar Law는 `U → T`를 제공한다. 뒷문은 열린 채 남는다.

**정량 점검**(`confounding_demo.py`): 기사에는 측정값이 없어 실제 효과를 추정할 수 없지만, 뒷문 기준을 숫자로 보일 수는 있다. DAG를 따르고 `T → O`의 실제 효과를 **0으로** 심은 20만 건을 시뮬레이션하면, `U`를 무시한 보정 전 추정은 가짜 위험차 **+0.49**, **뒷문 보정** 추정은 **−0.00**(진실 회복)을 낸다. 겉보기 효과 전부가 기사가 결코 측정하지 않은 변수에 의한 교란 편향이다.

이것이 새로운 사례에서 본 예제의 핵심이다: 1단 증거도 식별 전략도 없이 서 있는 확신에 찬 역사적 *"because"*. **결론을 바꿀 증거:** 날짜를 특정할 수 있는 결정들 주변의 연맹 위상 시계열과 강대국 개입 수준 대용변수(`U`)가 있으면, 뒷문 보정이나 페르시아 표결을 둘러싼 이중차분(difference-in-differences) 설계가 가능해진다.

---

## 제출물 (과제 요구사항 대응)

1. **코드 / 노트북** — `src/`, `run_pipeline.py`, `notebook.ipynb`.
2. **지식그래프 내보내기** — `outputs/nodes.csv`, `outputs/edges.csv`, `outputs/ekg.graphml`.
3. **인과 다이어그램** — `figures/causal_dag.png` (한글판 포함).
4. **보고서** — `report.docx` / `report_ko.docx` (서식 보고서; `*.pdf`는 미리보기). 본 README는 그 내용을 그대로 담는다(0–7장).

## 솔직한 한계

규칙 기반 추출은 암시적 인과를 놓치고 일부 OCR을 잘못 분할한다. `U`는 텍스트로부터 논증된 질적 교란요인일 뿐 측정된 변수가 아니어서 식별 주장은 추정이 아니라 추론이다. "신뢰"라는 결과는 지표가 아니라 언론의 수사다. 이 한계들을 명시함으로써 분석이 어디까지 닿는지를 분명히 했다 — 그것이 이 파이프라인 전체가 가르치려는 규율이다.

**자료 출처:** 미국 의회도서관 *Chronicling America*(*Evening Star*, LCCN `sn83045462`), 1920년 6월 17일. 퍼블릭 도메인.
                      