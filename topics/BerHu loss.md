---
tags:
  - LossFunction
---
[[Huber loss]]를 뒤집은 형태의 손실 함수다.

오차 $x$가 임계값 $c$보다 작거나 같은 경우 [[L1 loss]] 처럼, 더 큰 경우 [[L2 loss]] 처럼 동작한다. Huber와 정확히 반대 구간에서 반대로 동작하기에 reverse Huber, 줄여서 BerHu라 부른다.

$$
\mathcal{B}(x)=
\begin{cases}
|x| & |x|\le c\\[4pt]
\dfrac{x^{2}+c^{2}}{2c} & |x|>c
\end{cases}
$$

$c$는 보통 배치 내 최대 오차의 20%($c = \frac{1}{5}\max_i|x_i|$)로 잡아 학습이 진행되며 오차가 줄어들면 임계값도 함께 줄어들게 한다. $|x|=c$ 에서 값과 1차 미분이 모두 연속이다.

Outlier가 많지 않고, 데이터 대부분이 신뢰할 만한 값을 가지는데 약간씩 흐릿한 상태인 경우 작은 오차에 더 큰 상대 그래디언트를 줘 경계를 선명하게 만드는 역할을 한다.

- L1 구간(작은 오차): 그래디언트 크기가 1로 유지되어 미세한 오차도 끝까지 밀어붙인다. L2였다면 오차에 비례해 그래디언트가 0으로 사라져 흐릿한 상태에서 학습이 멈춘다.
- L2 구간(큰 오차): 큰 오차에는 확실히 큰 페널티를 준다.

[[Depth Map]] 추정처럼 GT가 대체로 신뢰할 만하고 문제는 경계가 뭉개지는 것(regression-to-the-mean)인 과제에서 효과적이다. 반대로 GT 자체에 outlier가 많다면 [[Huber loss]] 나 다른 [[Robust loss function]] 을 써야 한다.

## Reference
Laina et al. *Deeper Depth Prediction with Fully Convolutional Residual Networks*. 3DV 2016.
