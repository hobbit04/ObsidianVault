---
title: |-
  SPIDER: Scalable Physics-Informed
  Dexterous Retargeting
School:
  - Carnegie Mellon University
Lab:
  - FAIR at Meta
tags:
  - 3D
  - Robotics
---
## Task
> How can we efficiently and reliably transform human motion into feasible robot trajectories that respect dynamics and contact?

사람의 손 모션 데이터를 어떻게 로봇에 대입시킬 수 있을까에 대한 답을 제시한다. [[Do as I do]]에서의 reconstruction에 집중하는 것으로 볼 수 있다. 
## Method
크게 네 단계로 나누어 설명한다. 문제를 정의하고, 해결하는 방법을 제시하고, 효율과 퀄리티를 높이는 기법을 소개한 다음 마지막으로 시뮬레이션과 현실의 차이를 좁히기 위한 방법을 제시한다.
### Physics-based retargeting problem
어떻게 물리를 기반으로 retargeting을 해야 하는지, 최적화 문제로 먼저 정의한다. 
Retargeting의 최종 output은 $u_{0:T-1}$로, robot control sequence이다. 이는 두 가지 기준을 갖고 최적화 된다.
1. Distance to the reference trajectory
2. Control effort
추가로 terminal 오차 항도 들어있다. 
![[Pasted image 20260908150024.png]]
맨 위의 수식이 최적화 식이다. 첫번째 항은 terminal(종료) 항으로, 마지막 상태가 얼마나 reference와 유사한지를 판단하기 위함이다. $u$는 토크들을 벡터 형태로 저장한 것이라 어떤 "원인"으로 해석할 수 있다. 위치 $x$는 "결과"로 볼 수 있고, 두번째 식에서 그 관계가 나온다. 원본 궤적과의 차이는 매 timestep 계산되고, Control effort도 더해진다. Control effort는 토크가 얼마나 강하게 걸리는지로, 필요할 때만 관절에 힘(토크)을 줘야함을 반영한 것이다.
$||\cdot||^2_{Q_t}$는 Weighted quadratic norm으로, $z^TQ_t z$를 의미한다. 식을 보면 각각 $Q_t, R_t$가 있는데 이는 대각행렬로 정의되며 state, control input weighting 행렬이다. 
### Sampling for Physics-based Retargeting
위의 최적화 목적함수 수식은 매우 non-convex & non-continuous 하다. 이를 해결하기 위해선 Sampling based로 최적화 문제를 접근해야 한다. 강화학습으로 접근하면 $\pi_\theta$라는 정책 네트워크를 학습해야 하는데, 여기선 샘플링 방식으로 control sequence 만 수정해나간다. 그래서 "10x faster than RL" 이라는 주장을 펼친다. 
$$U^{i+1}=U^{i}+\frac{\sum_{j=1}^{N_W}\exp\left(-\frac{J(U^i+[W]_j)}{\lambda}\right)[W]_j}{\sum_{j=1}^{N_W}\exp\left(-\frac{J(U^i+[W]_j)}{\lambda}\right)}
$$
이때 $[W]_j$는 가우시안 노이즈를 의미한다. 노이즈의 공분산을 고정하지 않고 스케줄링 하는 것이 이 논문의 첫 번째 기여라고 할 수 있다. 
### Virtual Contact Guidance
위의 최적화를 푼 결과는 꼭 하나의 답이 아닐 수도 있다. 그래서 local minima에 머물 수 있는데, 이를 해결하기 위해 virtual contact guidance를 도입한다. 
![[Pasted image 20260910184244.png]]
(a)는 똑같은 목적을 달성하는 행동이더라도 사람의 방식을 선호 하도록 contact guidance를 주는 예시이다. (b)는 노이즈의 공분산을 고정하지 않는, annealed kernel을 사용한 sampling과 더불어 contact guidance를 사용했을 때의 샘플링 효용이 올라가는 것을 나타내는 그림이다. 
