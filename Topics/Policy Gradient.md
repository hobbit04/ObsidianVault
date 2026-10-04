---
tags:
  - ReinforcementLearning
  - Algorithm
---
정책 $\theta$를 직접적으로 구하는 방법을 총칭하는 말이다.

성능을 나타내는 어떤 지표 $J$가 있을 때, $J(\theta)$를 최대화 시키기 위한 업데이트 식은 다음과 같다.
$$\theta_{t+1}=\theta_t+\alpha\hat{\nabla J(\theta_t)}$$여기서 $\alpha$에 곱해진 항은 실제 그래디언트의 근사값으로, 샘플을 이용해 추정하는 값이다. 