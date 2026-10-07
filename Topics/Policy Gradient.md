---
tags:
  - ReinforcementLearning
  - Algorithm
---
[[RL_book.pdf]]

정책 $\theta$를 직접적으로 구하는 방법을 총칭하는 말이다.

성능을 나타내는 어떤 지표 $J$가 있을 때, $J(\theta)$를 최대화 시키기 위한 업데이트 식은 다음과 같다.
$$\theta_{t+1}=\theta_t+\alpha\hat{\nabla J(\theta_t)}$$여기서 $\alpha$에 곱해진 항은 실제 그래디언트의 근사값으로, 샘플을 이용해 추정하는 값이다. 

## Policy Gradient Theorem
$\nabla J$를 직접 구하는 것은 불가능하고 *policy gradient theorem* 을 이용해 계산한다. $$\nabla_\theta J=\mathbb{E}_{s,a \sim \pi_\theta}[\nabla_\theta \log{\pi_\theta(a|s)}\cdot A^\pi(s,a)]$$
여기서 $A^\pi$는 Advantage를 의미하며, 식으로는 $Q-V$가 된다. 원래 policy gradient theorem 식에는 $Q$가 등장하는데, state에만 의존하는 함수는 어떤 함수든 빼도 그래디언트의 기댓값이 변하기 않기 때문에 state에 대한 함수인 $V(s)$를 빼도 괜찮은 것이다. 이렇게 식을 만들면 분산이 크게 줄어드는 효과가 있다.  
## How to estimate an Advantage
실제로는 $Q$를 학습하지 않고 $V$만을 이용해 $A$를 추정한다. 
- One step TD-error: $\delta_t = r_t + \gamma V(s_{t+1})-V(s_t)$ 
- GAE: $\hat{A_t}=\delta_t+\gamma \lambda \hat{A}_{t+1}$ 
