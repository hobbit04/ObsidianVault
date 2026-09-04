---
title: Learning Dexterous Manipulation Using Contact Wrench Guidance From Human Demonstration
tags:
  - Robotics
  - 3D
  - paper
  - ReinforcementLearning
---
*사람의 손과 로봇의 손은 다른 점들이 많지만, 물체와 접촉하고 힘을 주는 원리는 동일하다는 아이디어에서 wrench space 라는 공간에서 둘을 대응시키려고 한다.*
## Task
Human video data를 바탕으로 로봇이 학습할 수 있는 데이터를 구축하는 것을 목표로 한다. 
## Previous Limits
- Contact location을 기준으로 보상을 주는 RL 학습 환경을 구축. 접점은 같아도 힘의 방향이 다를 수 있어 제대로 학습이 안됨. 
	- DexMachina, SPIDER 계열. VOC(virtual object controller)로 초기 탐색을 쉽게 만들지만, 그 대가로 실질적 효과가 없는 접촉 행동에 수렴하는 local optima 문제가 생긴다.
	- 사람 손과 로봇 손의 접촉점 개수·위치가 다르면(5지 ↔ 3지) 위치 매칭 자체가 원리적으로 불가능하다.
- Contact force를 기준으로 보상을 주는 방식(ManipTrans). 시연된 hand-object interaction 근처의 힘에 보상을 주지만, 여전히 물체 수준에서의 효과를 보는 것은 아니다.
- Wrench space 자체는 새로운 개념이 아니다. 다만 쓰임새가 달랐다.
	- 고전 파지 역학(Bicchi, Ferrari-Canny)에서 **force closure 판정용 지표**로 사용. "이 파지가 임의의 외란을 버틸 수 있는가"를 재는 도구였다.
	- 이를 그대로 RL 보상으로 가져온 연구들(Melnik, Merzic, Koenig 등)은 결국 **static stability를 최대화**하는 목적함수가 된다.
	- 한계 1: 조작(manipulation)의 목적은 버티는 것이 아니라 물체를 원하는 대로 **움직이는 것**이다. 목적함수가 근본적으로 어긋나 있다.
	- 한계 2: force closure 가정이 너무 경직되어 있다. 장기 조작에는 pushing, levering, sliding처럼 force closure가 성립하지 않는 과도기 구간이 반드시 존재하는데, 이를 전부 나쁜 접촉으로 벌점 처리한다.
	- 한계 3: 참조(reference) 없이 그 자체로 좋고 나쁨을 매기는 **절대적 품질 지표**였다. 사람 시연과 로봇 실행을 비교하는 척도로 쓰인 적이 없다.
	- 한계 4: 단일 강체 파지를 전제하므로 articulated object에 적용할 수 없다.

> [!note] 이 논문의 전환점
> Wrench space를 **품질 함수(quality function)에서 대응 함수(correspondence function)로 재해석**한 것. 안정성을 최대화하는 대신, 사람 시연의 wrench와 로봇의 wrench가 얼마나 닮았는지를 잰다. 덕분에 접촉 위치·개수·손 형태가 달라도 "물체에 어떤 운동을 유발하는가"라는 공통 언어로 비교할 수 있고, non-force-closure 과도 구간도 자연스럽게 허용된다.
> 이를 가능하게 한 기술적 장치가 support function이다. 열 개수와 순서가 제각각인 두 wrench matrix를 고정 길이 $b$차원 벡터로 정렬시켜 비교 가능하게 만든다.
## Method
기본적으로 [[PPO]] 방식의, 정책을 학습하는 알고리즘이고 reward를 설계하는 것에 가장 큰 공을 들인다. 
### RL with Wrench Space Contact Guidance
총 세 개의 보상을 사용한다.
1. **Task tracking.** Object가 이동하는 경로가 주어진 reference와 일치하는 정도를 따진다.
2. **Motion imitation.** Human 키포인트들과 로봇의 키포인트가 일치하는 정도를 따진다. 이때 human 키포인트들은 [[Inverse Kinematics]]과정을 거쳐 로봇 기준($x_t^\text{robot}$)으로 바꾼다.
3. **Contact guidance.** 매 타임스텝마다 $\mathcal{W}_{h,k}$를 만든 후 이의 support function을 정의한다. 그 다음 human reference function과 robot support function을 비교해 $r_\text{cws}$라는 contact loss를 만든다. 

이 보상들을 합쳐서 $r$로 사용한다. [[VOC]]를 사용해 학습 초기에 너무 보상이 sparse 하지 않도록 도와준다.
