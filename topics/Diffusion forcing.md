---
tags:
  - ComputerVision
---
**Title: Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion**
## Introduction
---
- Teacher forcing: Ground truth를 이용해 바로 다음 토큰을 예측하는 방식
	한계;
	1. Sequence를 샘플링할 때 어떤 목적 함수를 최소화 시키는 방향으로 guide를 줄 방법이 없다
	2. 연속 데이터에 대해서는 쉽게 불안정해진다. Error가 누적되기 때문
- Full-sequence diffusion: 일정 수의 토큰을 concat 한 후 diffusion 시켜 joint distribution을 모델링 하는 방식
	 Diffusion guidance를 샘플링시 사용할 수 있고 가속화도 시킬 수 있음. 하지만 인과관계가 없고 마스킹되지 않은 구조로 파라미터화 되어 있어서 guidance와 subsequence 생성에 제한이 된다. 

이 두 방식을 합치면 어떨까? Naive하게 접근하면 오히려 성능이 떨어짐. 이전 토큰의 불확실성이 이후 토큰 생성에는 더 큰 불확실성으로 이어진다는 사실을 모델링 하지 못하기 때문이다. 
- Diffusion Forcing: 각 토큰이 무작위의 독립적인 noise level에서 훈련 및 샘플링 되는 방식
	노이즈가 포함된 토큰은 partially masking된 토큰으로 볼 수 있다는 점에서 착안. 
	논문에서는 미래 토큰을 과거 토큰에 의존적으로 생성하는 Causal Diffusion Forcing(CDF)를 제시했으며 대부분의 내용이 CDF 설명임. Guidance 뿐만 아니라 MCG도 사용이 가능해졌음.
## Method
---
### Noising as partial masking
Masking에 대해서 두 가지 축을 제시한다. 첫번째 축은 시간축이고, 다른 한 축은 noise축이다. 마스킹은 (실제로 시간 순서가 상관이 없더라도) t축을 따라 배치된 토큰들의 ordered set에서 이루어졌다. 1:t-1 토큰들을 이용해 마스킹된 t 토큰을 예측하는 식. 

이 논문에서 제시하는 관점은 full-sequence forward diffusion을 noise 축으로의 마스킹으로 보는 관점이다. $x_{1:T}$, 즉 전체 토큰을 $k_t$로 인덱싱 해 노이즈 축에서의 변화를 특정한다. 하나의 토큰 $x$에 $t, k_t$를 모두 사용함으로써 두 방향으로의 마스킹을 표현할 수 있다. 

![[Pasted image 20250717201935.png]]

### Diffusion Forcing: different noise levels for different tokens
각 토큰의 노이즈 레벨은 time step에 따라 달라진다. 이때 time step이 같아도 토큰에 따라 노이즈 레벨이 달라질 수 있고 이 사실이 해당 논문에서 가장 중요하게 작용하는 부분이다.

시계열 데이터에 집중해서 설명을 하며, 따라서 CDF가 사용된다. 구현의 편리함을 위해 바닐라 RNN에서 적용시켰다. 
![[Pasted image 20250717234440.png]]
**알고리즘 설명**
**Diffusion forcing Training**
	 ![[Pasted image 20250721155233.png|200]]
	 먼저 trajectory $(x_1, ..., x_T)$를 샘플링 함. 
	 $t=1$ ~ $T$까지 반복:
		 이번 timestep에 사용할 노이즈 레벨을 uniform하게 샘플링해서 $k_t$에 저장
		 $x_t^{k_t}$: t번째 토큰에 $k_t$만큼의 노이즈를 추가한 벡터
		 $\epsilon_t$: ForwardDiffuse 과정에서 실제로 추가된 노이즈
		 $z_t$: RNN unit의 hidden state 역할을 하는 latent vector로, 과거의 latent와 노이즈가 추가된 벡터, 그리고 노이즈 레벨을 바탕으로 현재 time step의 latent(hidden state)를 샘플링한다
		 $\hat{\epsilon}_t$: 이전 latent, $x_t^{k_t}$, 그리고 노이즈 레벨을 이용해 모델이 예측한 노이즈
	 모델이 예측한 노이즈와 실제 노이즈를 비교해 MSELoss를 계산하고 이를 바탕으로 파라미터를 학습
	 -> 다양한 노이즈 레벨에서의 노이즈 예측기를 학습하는 것이 목표
**DF Sampling with Guidance**
	 ![[Pasted image 20250721160416.png|200]]
	 정규분포에서 샘플링 한 노이즈를 모든 time step에서의 토큰의 초기값으로 설정
	 for row m = M - 1,...,0:
		 위에 줄(row)부터 아래로 내려가며 노이즈 스케쥴에 맞게 노이즈 제거 과정을 거침
		 for t = 1, ... T:
			 $z_t^\text{new}$: 이전 latent, 현재 토큰, 그리고 노이즈 스케쥴 값을 이용해 현재 time step에 해당하는 latent를 샘플링 함
			 $k$: 노이즈 레벨. 스케쥴링 matrix에서 (m, t)에 해당하는 값을 가져오면 됨
			 $w$: Stochastic term. 정규분포에서 샘플링 해온다
			 $\sigma_k$: diffusion coefficient. 노이즈 레벨(k)에 따라 값이 정해진다
		 하나의 row에 대해 토큰 디노이즈 과정이 끝났다면 guidance를 준다. 

**Training**
- Dynamics model: $p_\theta (z_t|z_{t-1}, x_t^{k_t}, k_t)$, 이전 time step의 latent vector와 노이즈가 포함된 이미지를 이용해 t time step의 latent vector를 만들어낸다. 
- Observation model: $p_\theta(x_t^0|z_t)$, latent vector를 이용해 원본 이미지에 해당하는 확률 분포를 표현한다.
이 두 모델을 결합해 RNN unit을 만들었다. 

디퓨전 모델의 input-output과 동일하기 때문에 diffusion 학습 시 사용하는 목적 함수를 그대로 사용할 수 있다. 

**Sampling**
2차원 행렬의 noise schedule을 이용한다. $\mathcal{K} \in [K]^{M\times T}$ 를 어떻게 디자인 하느냐에 따라 모델을 재학습하지 않고도 다른 behaviors를 보이게 할 수 있다. 디퓨전 스텝의 속도와 관련이 있기 때문 

### New Capabilities in Sequence Generation
![[Pasted image 20250718000108.png]]
- AR 생성의 안정화: 약간 노이즈가 있는 이전 토큰의 latent를 이용해 계속해서 latent를 업데이트하기 때문에 안정적으로 긴 시퀀스를 roll out 할 수 있다. 
- 미래 불확실성의 유지: 디노이즈를 각 토큰마다 다른 정도로 할 수 있다. 즉 같은 time step이라도 노이즈 레벨을 다르게 할 수 있음. 이때 가까운 미래는 바로 디노이즈 시키고 먼 미래는 조금만 또는 전혀 디노이즈 하지 않음으로써 먼 미래에 대한 불확실성을 유지할 수 있다.
- Long-horizon guidance: Sampling 과정에서 guidance를 줄 수 있는데, 기존의 full-sequence 모델과는 달리 미래의 gradient를 과거 토큰이 이용할 수 있음. 같은 time step에서도 다른 노이즈 레벨을 가질 수 있기 때문. 
### Diffusion Forcing for Flexible Sequential Decision Making
$x_t=[a_t,r_t,o_{t+1}]$로 토큰을 정의해서 Sequential Decision Making 프레임워크를 만들 수 있다. 이 경우 MDP의 trajectory를 $x_{1:T}$라는 sequence가 하게 된다. 
**Flexible planning horizon**: lookahead window의 크기를 줄이면 policy로 사용할 수 있고 늘이면 planning으로 사용할 수 있다. 
**Flexible reward guidance**: 미래 토큰의 gradient가 현재 토큰에 디노이징에 영향을 줄 수 있기 때문에, goal completion 등의 spars한 reward도 목적함수로 사용할 수 있다.
**MCG, future uncertainty**: CFG 덕분에 $x_t^k$가 미래 토큰 분포 즉 $x_{t+1:T}$의 guidance를 이용해 생성될 수 있다. 이때 하나의 궤적($x_{t+1:T}$)만 이용할 필요 없이 여러 샘플을 만들고 평균을 낸 다음 이를 guidance로 활용할 수도 있다. 이를 Monte Carlo Guidance라고 한다. 

## Experiments
---
### Video Prediction
- 사용한 모델: Convolutional RNN기반의 CDF
- 목적: Minecraft gameplay & DMLab navigation video를 기반으로한 비디오 생성
- 방식: 샘플링시 autoregressive rollout with stabilization 사용
- 비교: Full-sequence vs DF
DF가 긴 영상 생성에 대해서 더 좋은 성능을 보여줌. 
### Diffusion Planning: MCG, Causal Uncertainty, Flexible Horizon Control
- 사용한 벤치마크: D4RL의 2D maze 환경
- 비교: Sota offline RL model vs Diffuser(diffusion planning framework) vs DF
**MCG**를 이용하면 RL 문제의 핵심인 *미래 보상 기댓값을 최대화 시키는 action 수행*을 해결할 수 있다. MCG 없이 DF 모델을 학습 시켰더니 성능은 떨어졌지만, 그럼에도 sota 모델과 비슷한 정도의 성능을 보였다.
**Causal Uncertainty**를 고려하는 DF 모델은 Diffuser가 planning을 위해 만든 비디오 + Handcrafted된 PD controller 보다 좋은 성능을 냈다.
강화학습 task는 대부분 **Flexible horizon**을 요구한다. Step 수가 고정된 환경의 경우 진행됨에 따라 horizon이 점점 줄어들기 때문인데, DF는 노이즈를 다르게 줄 수 있으므로 자연스럽게 이를 만족시킬 수 있는 반면 Diffuser 모델은 변형을 가해도 좋은 성능을 내지 못한다.

### Controllable Sequential Compositional Generation
![[Pasted image 20250718152530.png]]
### Robotics: Long horizon imitation learning and robust visuomotor control
- Visuomotor: visual + motor

## Limitations and Questions
---
1. 미래 토큰에서의 Guidance gradients가 시간을 거슬러 back propagate 될 수 있다는 부분이 이해가 잘 안됐음.
2. 샘플링 때 사용하는 noise schedule matrix를 사람이 task에 따라 직접 작성해줘야 한다는 점이 아쉬움.